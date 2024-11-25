#!/usr/bin/env python3
# Copyright 2024 Canonical
# See LICENSE file for licensing details.

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

https://discourse.charmhub.io/t/4208
"""

import hashlib
import logging
import socket
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlparse

import cosl.coordinated_workers.nginx
import ops
import yaml
from charms.alertmanager_k8s.v1.alertmanager_dispatch import AlertmanagerConsumer
from charms.grafana_k8s.v0.grafana_source import GrafanaSourceProvider
from charms.loki_k8s.v1.loki_push_api import LokiPushApiProvider
from charms.tempo_coordinator_k8s.v0.charm_tracing import trace_charm
from charms.tempo_coordinator_k8s.v0.tracing import charm_tracing_config
from charms.traefik_k8s.v2.ingress import IngressPerAppReadyEvent, IngressPerAppRequirer
from cosl.coordinated_workers.coordinator import Coordinator
from ops.model import ModelError
from ops.pebble import Error as PebbleError

from loki_config import LOKI_ROLES_CONFIG, LokiConfig
from nginx_config import NginxConfig

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

RULES_DIR = "/etc/loki-alerts/rules"
ALERTS_HASH_PATH = "/etc/loki-alerts/alerts.sha256"


@trace_charm(
    tracing_endpoint="charm_tracing_endpoint",
    server_cert="server_ca_cert",
    extra_types=[
        Coordinator,
    ],
)
class LokiCoordinatorK8SOperatorCharm(ops.CharmBase):
    """Charm the service."""

    def __init__(self, *args: Any):
        super().__init__(*args)

        self._nginx_container = self.unit.get_container("nginx")
        self._nginx_prometheus_exporter_container = self.unit.get_container(
            "nginx-prometheus-exporter"
        )
        self.ingress = IngressPerAppRequirer(
            charm=self,
            port=urlparse(self.internal_url).port,
            strip_prefix=True,
            scheme=lambda: urlparse(self.internal_url).scheme,
        )
        self.alertmanager_consumer = AlertmanagerConsumer(self, relation_name="alertmanager")
        self.coordinator = Coordinator(
            charm=self,
            roles_config=LOKI_ROLES_CONFIG,
            external_url=self.external_url,
            worker_metrics_port=3100,
            endpoints={
                "certificates": "certificates",
                "cluster": "loki-cluster",
                "grafana-dashboards": "grafana-dashboards-provider",
                "logging": "logging-consumer",
                "metrics": "self-metrics-endpoint",
                "charm-tracing": "charm-tracing",
                "workload-tracing": "workload-tracing",
                "s3": "s3",
            },
            nginx_config=NginxConfig().config,
            workers_config=LokiConfig(
                alertmanager_urls=self.alertmanager_consumer.get_cluster_info()
            ).config,
            workload_tracing_protocols=["jaeger_thrift_http"],
        )

        self.charm_tracing_endpoint, self.server_ca_cert = charm_tracing_config(
            self.coordinator.charm_tracing, cosl.coordinated_workers.nginx.CA_CERT_PATH
        )

        self.grafana_source = GrafanaSourceProvider(
            self,
            source_type="loki",
            source_url=self.external_url,
            extra_fields={"httpHeaderName1": "X-Scope-OrgID"},
            secure_extra_fields={"httpHeaderValue1": "anonymous"},
            refresh_event=[self.coordinator.cluster.on.changed],
        )

        external_url = urlparse(self.external_url)
        self.loki_provider = LokiPushApiProvider(
            self,
            address=external_url.hostname or self.hostname,
            port=external_url.port or 443 if self.coordinator.tls_available else 8080,
            scheme=external_url.scheme,
            path=f"{external_url.path}/loki/api/v1/push",
        )

        if self._nginx_container.can_connect():
            self._set_alerts()

        ######################################
        # === EVENT HANDLER REGISTRATION === #
        ######################################
        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)
        self.framework.observe(self.on.nginx_pebble_ready, self._on_pebble_ready)

    ##########################
    # === EVENT HANDLERS === #
    ##########################
    def _on_ingress_ready(self, event: IngressPerAppReadyEvent):
        """Log the obtained ingress address.

        This event refreshes the PrometheusRemoteWriteProvider address.
        """
        logger.info("Ingress for app ready on '%s'", event.url)

    def _on_ingress_revoked(self, _) -> None:
        """Log the ingress address being revoked.

        This event refreshes the PrometheusRemoteWriteProvider address.
        """
        logger.info("Ingress for app revoked")

    def _on_pebble_ready(self, _) -> None:
        """Make sure the `lokitool` binary is in the workload container."""
        self._ensure_lokitool()

    ######################
    # === PROPERTIES === #
    ######################

    @property
    def hostname(self) -> str:
        """Unit's hostname."""
        return socket.getfqdn()

    @property
    def internal_url(self) -> str:
        """Returns workload's FQDN. Used for ingress."""
        scheme = "http"
        if hasattr(self, "coordinator") and self.coordinator.nginx.are_certificates_on_disk:
            scheme = "https"
        return f"{scheme}://{self.hostname}:8080"

    @property
    def external_url(self) -> str:
        """Return the external hostname to be passed to ingress via the relation."""
        try:
            if ingress_url := self.ingress.url:
                return ingress_url
        except ModelError as e:
            logger.error("Failed obtaining external url: %s.", e)
        return self.internal_url

    ###########################
    # === UTILITY METHODS === #
    ###########################

    def _pull(self, path: str) -> Optional[str]:
        """Pull file from container (without raising pebble errors).

        Returns:
            File contents if exists; None otherwise.
        """
        try:
            return cast(str, self._nginx_container.pull(path, encoding="utf-8").read())
        except (FileNotFoundError, PebbleError):
            # Drop FileNotFoundError https://github.com/canonical/operator/issues/896
            return None

    def _push(self, path: str, contents: Any):
        """Push file to container, creating subdirs as necessary."""
        self._nginx_container.push(path, contents, make_dirs=True, encoding="utf-8")

    def _push_alert_rules(self, alerts: Dict[str, Any]) -> List[str]:
        """Pushes alert rules from a rules file to the nginx container.

        Args:
            alerts: a dictionary of alert rule files, fetched from
                either a metrics consumer or a remote write provider.
        """
        paths = []
        for topology_identifier, rules_file in alerts.items():
            filename = f"juju_{topology_identifier}.rules"
            path = f"{RULES_DIR}/{filename}"

            rules = yaml.safe_dump(rules_file)

            self._push(path, rules)
            paths.append(path)
            logger.debug("Updated alert rules file %s", filename)

        return paths

    def _ensure_lokitool(self):
        """Copy the `lokitool` binary to the workload container."""
        if self._nginx_container.exists("/usr/bin/mimirtool"):
            return
        with open("lokitool", "rb") as f:
            self._nginx_container.push("/usr/bin/lokitool", source=f, permissions=0o744)

    def _set_alerts(self):
        """Create alert rule files for all Loki consumers."""

        def sha256(hashable: Any) -> str:
            """Use instead of the builtin hash() for repeatable values."""
            if isinstance(hashable, str):
                hashable = hashable.encode("utf-8")
            return hashlib.sha256(hashable).hexdigest()

        # Get mimirtool if this is the first execution
        self._ensure_lokitool()

        loki_alerts = self.loki_provider.alerts
        alerts_hash = sha256(str(loki_alerts))
        alert_rules_changed = alerts_hash != self._pull(ALERTS_HASH_PATH)

        if alert_rules_changed:
            # Update the alert rules files on disk
            self._nginx_container.remove_path(RULES_DIR, recursive=True)
            rules_file_paths: List[str] = self._push_alert_rules(loki_alerts)
            self._push(ALERTS_HASH_PATH, alerts_hash)
            # Push the alert rules to the Mimir cluster (persisted in s3)
            logger.info(
                f"lokitool rules sync {' '.join(rules_file_paths)} --address={self.external_url}/loki --id=fake"
            )
            lokitool_output = self._nginx_container.pebble.exec(
                [
                    "lokitool",
                    "rules",
                    "sync",
                    *rules_file_paths,
                    f"--address={self.external_url}",
                    "--id=fake",  # multitenancy is disabled, the default tenant is 'fake'
                ],
                encoding="utf-8",
            )
            if lokitool_output.stdout:
                logger.info(f"lokitool: {lokitool_output.stdout.read().strip()}")
            if lokitool_output.stderr:
                logger.error(f"lokitool (err): {lokitool_output.stderr.read().strip()}")


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(LokiCoordinatorK8SOperatorCharm)
