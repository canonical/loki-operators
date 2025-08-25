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

import ops
import yaml
from charms.alertmanager_k8s.v1.alertmanager_dispatch import AlertmanagerConsumer
from charms.catalogue_k8s.v1.catalogue import CatalogueItem
from charms.grafana_k8s.v0.grafana_source import GrafanaSourceProvider
from charms.loki_k8s.v1.loki_push_api import LokiPushApiProvider
from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer
from coordinated_workers.coordinator import Coordinator
from coordinated_workers.nginx import NginxConfig
from cosl.interfaces.datasource_exchange import DatasourceDict
from ops.model import ModelError
from ops.pebble import Error as PebbleError

from loki_config import LOKI_ROLES_CONFIG, LokiConfig
from nginx_config import NginxHelper

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

RULES_DIR = "/etc/loki-alerts/rules"
ALERTS_HASH_PATH = "/etc/loki-alerts/alerts.sha256"
NGINX_PORT = NginxHelper._nginx_port
NGINX_TLS_PORT = NginxHelper._nginx_tls_port



class LokiCoordinatorK8SOperatorCharm(ops.CharmBase):
    """Charm the service."""

    def __init__(self, *args: Any):
        super().__init__(*args)

        self._nginx_container = self.unit.get_container("nginx")
        self._nginx_prometheus_exporter_container = self.unit.get_container(
            "nginx-prometheus-exporter"
        )
        self._nginx_helper = NginxHelper(self._nginx_container)
        self.ingress = IngressPerAppRequirer(
            charm=self,
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
                "send-datasource": "send-datasource",
                "receive-datasource": None,
                "catalogue": None,
            },
            nginx_config=NginxConfig(
                server_name=self.hostname,
                upstream_configs=self._nginx_helper.upstreams(),
                server_ports_to_locations=self._nginx_helper.server_ports_to_locations(),
                enable_health_check=True,
                enable_status_page=True,
            ),
            workers_config=LokiConfig(
                alertmanager_urls=self.alertmanager_consumer.get_cluster_info()
            ).config,
            worker_ports=lambda _: tuple({3100}),
            resources_requests=self.get_resource_requests,
            container_name="nginx",  # container to which resource limits will be applied
            workload_tracing_protocols=["jaeger_thrift_http"],
            catalogue_item=self._catalogue_item,
        )

        # needs to be after the Coordinator definition in order to push certificates before checking
        # if they exist
        if port := urlparse(self.internal_url).port:
            self.ingress.provide_ingress_requirements(port=port)

        self.grafana_source = GrafanaSourceProvider(
            self,
            source_type="loki",
            source_url=self.external_url,
            extra_fields={"httpHeaderName1": "X-Scope-OrgID"},
            secure_extra_fields={"httpHeaderValue1": "anonymous"},
            refresh_event=[
                self.coordinator.cluster.on.changed,
                self.on[self.coordinator._certificates.relationship_name].relation_changed,
                self.ingress.on.ready,
                self.ingress.on.revoked,
            ],
            is_ingress_per_app=self.ingress.is_ready(),
        )

        external_url = urlparse(self.external_url)
        self.loki_provider = LokiPushApiProvider(
            self,
            address=external_url.hostname or self.hostname,
            port=external_url.port or NGINX_TLS_PORT
            if self.coordinator.tls_available
            else NGINX_PORT,
            scheme=external_url.scheme,
            path=f"{external_url.path}/loki/api/v1/push",
        )

        # do this regardless of what event we are processing
        self._reconcile()

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
        scheme, port = (
            ("https", NGINX_TLS_PORT)
            if hasattr(self, "coordinator") and self.coordinator.nginx.are_certificates_on_disk
            else ("http", NGINX_PORT)
        )
        return f"{scheme}://{self.hostname}:{port}"

    @property
    def external_url(self) -> str:
        """Return the external hostname to be passed to ingress via the relation."""
        try:
            if ingress_url := self.ingress.url:
                return ingress_url
        except ModelError as e:
            logger.error("Failed obtaining external url: %s.", e)
        return self.internal_url

    @property
    def _catalogue_item(self) -> CatalogueItem:
        """A catalogue application entry for this Loki instance."""
        return CatalogueItem(
            name="Loki",
            icon="text",
            url="",
            description=(
                "Loki provides a horizontally scalable, highly available, "
                "multi-tenant, log aggregation system. "
                "(no user interface available)"
            ),
        )

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
        """Copy the `lokitool` binary to the `nginx` container if it's not there already.

        Assumes the nginx container can connect.
        """
        if self._nginx_container.exists("/usr/bin/lokitool"):
            return
        with open("lokitool", "rb") as f:
            self._nginx_container.push("/usr/bin/lokitool", source=f, permissions=0o744)

    def _set_alerts(self):
        """Create alert rule files for all Loki consumers.

        Assumes the nginx container can connect.
        """
        # obtain lokitool if this is the first execution
        self._ensure_lokitool()

        def sha256(hashable: Any) -> str:
            """Use instead of the builtin hash() for repeatable values."""
            if isinstance(hashable, str):
                hashable = hashable.encode("utf-8")
            return hashlib.sha256(hashable).hexdigest()

        loki_alerts = self.loki_provider.alerts
        alerts_hash = sha256(str(loki_alerts))
        alert_rules_changed = alerts_hash != self._pull(ALERTS_HASH_PATH)

        if alert_rules_changed:
            # Update the alert rules files on disk
            self._nginx_container.remove_path(RULES_DIR, recursive=True)
            rules_file_paths: List[str] = self._push_alert_rules(loki_alerts)
            self._push(ALERTS_HASH_PATH, alerts_hash)
            # Push the alert rules to the Loki cluster (persisted in s3)
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

    def _update_datasource_exchange(self) -> None:
        """Update the grafana-datasource-exchange relations."""
        if not self.unit.is_leader():
            return

        # we might have multiple grafana-source relations, this method collects them all and returns a mapping from
        # the `grafana_uid` to the contents of the `datasource_uids` field
        # for simplicity, we assume that we're sending the same data to different grafanas.
        # read more in https://discourse.charmhub.io/t/tempo-ha-docs-correlating-traces-metrics-logs/16116
        grafana_uids_to_units_to_uids = self.grafana_source.get_source_uids()
        raw_datasources: List[DatasourceDict] = []

        for grafana_uid, ds_uids in grafana_uids_to_units_to_uids.items():
            for _, ds_uid in ds_uids.items():
                raw_datasources.append({"type": "loki", "uid": ds_uid, "grafana_uid": grafana_uid})
        self.coordinator.datasource_exchange.publish(datasources=raw_datasources)

    def get_resource_requests(self, _) -> Dict[str, str]:
        """Returns a dictionary for the "requests" portion of the resources requirements."""
        return {"cpu": "50m", "memory": "100Mi"}

    def _reconcile(self):
        # This method contains unconditional update logic, i.e. logic that should be executed
        # regardless of the event we are processing.
        if self._nginx_container.can_connect():
            self._set_alerts()

        self._update_datasource_exchange()


if __name__ == "__main__":  # pragma: nocover
    ops.main(LokiCoordinatorK8SOperatorCharm)
