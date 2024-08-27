#!/usr/bin/env python3
# Copyright 2024 Canonical
# See LICENSE file for licensing details.

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

https://discourse.charmhub.io/t/4208
"""

import glob
import logging
import os
import shutil
import socket
from typing import Any, Optional
from urllib.parse import urlparse

import cosl.coordinated_workers.nginx
import ops
from charms.alertmanager_k8s.v1.alertmanager_dispatch import AlertmanagerConsumer
from charms.grafana_k8s.v0.grafana_source import GrafanaSourceProvider
from charms.loki_k8s.v1.loki_push_api import LokiPushApiProvider
from charms.tempo_k8s.v1.charm_tracing import trace_charm
from charms.traefik_k8s.v2.ingress import IngressPerAppReadyEvent, IngressPerAppRequirer
from cosl.coordinated_workers.coordinator import Coordinator
from ops.model import ModelError

from loki_config import LokiConfig, LokiRolesConfig
from nginx_config import NginxConfig

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

NGINX_ORIGINAL_ALERT_RULES_PATH = "./src/prometheus_alert_rules/nginx"
WORKER_ORIGINAL_ALERT_RULES_PATH = "./src/prometheus_alert_rules/loki_workers"
CONSOLIDATED_ALERT_RULES_PATH = "./src/prometheus_alert_rules/consolidated_rules"


@trace_charm(
    tracing_endpoint="tempo_endpoint",
    server_cert="server_cert_path",
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
        self.coordinator = Coordinator(
            charm=self,
            roles_config=LokiRolesConfig(),
            s3_bucket_name="loki",
            external_url=self.external_url,
            worker_metrics_port=8080,
            endpoints={
                "certificates": "certificates",
                "cluster": "loki-cluster",
                "grafana-dashboards": "grafana-dashboards-provider",
                "logging": "logging-consumer",
                "metrics": "self-metrics-endpoint",
                "tracing": "tracing",
                "s3": "s3",
            },
            nginx_config=NginxConfig().config,
            workers_config=LokiConfig().config,
        )

        # FIXME: Should AlertmanagerConsumer it be in the Coordinator object?
        self.alertmanager_consumer = AlertmanagerConsumer(self, relation_name="alertmanager")
        self.grafana_source = GrafanaSourceProvider(
            self,
            source_type="loki",
            source_url=self.external_url,
            extra_fields={"httpHeaderName1": "X-Scope-OrgID"},
            secure_extra_fields={"httpHeaderValue1": "anonymous"},
            refresh_event=[self.coordinator.cluster.on.changed],
        )
        self._consolidate_nginx_rules()

        external_url = urlparse(self.external_url)
        self.loki_provider = LokiPushApiProvider(
            self,
            address=external_url.hostname or self.hostname,
            port=external_url.port or 443 if self.coordinator.tls_available else 8080,
            scheme=external_url.scheme,
            path=f"{external_url.path}/loki/api/v1/push",
        )

        ######################################
        # === EVENT HANDLER REGISTRATION === #
        ######################################
        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

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

    ######################
    # === PROPERTIES === #
    ######################

    @property
    def hostname(self) -> str:
        """Unit's hostname."""
        return socket.getfqdn()

    @property
    def tempo_endpoint(self) -> Optional[str]:
        """Tempo endpoint for charm tracing."""
        if self.coordinator.tracing.is_ready():
            return self.coordinator.tracing.get_endpoint(protocol="otlp_http")
        else:
            return None

    @property
    def server_cert_path(self) -> Optional[str]:
        """Server certificate path for tls tracing."""
        return cosl.coordinated_workers.nginx.CERT_PATH

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

    # FIXME: Move the alert_rules handling to Coordinator
    def _consolidate_nginx_rules(self):
        os.makedirs(CONSOLIDATED_ALERT_RULES_PATH, exist_ok=True)
        os.makedirs(CONSOLIDATED_ALERT_RULES_PATH, exist_ok=True)
        for filename in glob.glob(os.path.join(NGINX_ORIGINAL_ALERT_RULES_PATH, "*.*")):
            shutil.copy(filename, f"{CONSOLIDATED_ALERT_RULES_PATH}/")


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(LokiCoordinatorK8SOperatorCharm)
