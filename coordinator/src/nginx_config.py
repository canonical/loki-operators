# Copyright 2023 Canonical
# See LICENSE file for licensing details.
"""Nginx workload."""

import logging
from typing import Dict, List

from coordinated_workers.nginx import (
    CA_CERT_PATH,
    CERT_PATH,
    KEY_PATH,
    NginxLocationConfig,
    NginxUpstream,
)
from ops import Container

from loki_config import ROLES

logger = logging.getLogger(__name__)



class NginxHelper:
    """Helper class to generate the nginx configuration."""
    _loki_port = 3100
    _nginx_port = 8080
    _nginx_tls_port = 443

    _locations_write: List[NginxLocationConfig] = [
        NginxLocationConfig(path="/loki/api/v1/push", backend="write",modifier="="),
    ]

    _locations_backend: List[NginxLocationConfig] = [
        NginxLocationConfig(path="/loki/api/v1/rules", backend="backend",modifier="="),
        NginxLocationConfig(path="/prometheus/.*", backend="backend",modifier="~"),
        NginxLocationConfig(path="/api/v1/rules", backend="backend", backend_url="/loki/api/v1/rules",modifier="="),
    ]
    _locations_read: List[NginxLocationConfig] = [
        NginxLocationConfig(path="/loki/api/v1/tail", backend="read", modifier="="),
        NginxLocationConfig(path="/loki/api/.*", backend="read", modifier="~",headers={"Upgrade": "$http_upgrade", "Connection": "upgrade"})
    ]
    # Locations shared by all the workers, regardless of the role
    _locations_worker: List[NginxLocationConfig] = [
        NginxLocationConfig(path="/loki/api/v1/format_query", backend="worker",modifier="="),
        NginxLocationConfig(path="/loki/api/v1/status/buildinfo", backend="worker",modifier="="),
        NginxLocationConfig(path="/ring", backend="worker",modifier="="),
    ]

    def __init__(
        self,
        container: Container,
    ):
        self._container = container

    def upstreams(self) -> List[NginxUpstream]:
        """Generate the list of Nginx upstream metadata configurations."""
        upstreams = [NginxUpstream(role, self._loki_port, role) for role in ROLES]
        # add a generic `worker` upstream that routes to all workers
        upstreams.append(NginxUpstream("worker", self._loki_port, "worker", ignore_worker_role=True))
        return upstreams

    def server_ports_to_locations(self) -> Dict[int, List[NginxLocationConfig]]:
        """Generate a mapping from server ports to a list of Nginx location configurations."""
        return {
            self._nginx_tls_port if self._tls_available else self._nginx_port: self._locations_write + self._locations_backend + self._locations_read + self._locations_worker
        }

    @property
    def _tls_available(self) -> bool:
        return (
                self._container.can_connect()
                and self._container.exists(CERT_PATH)
                and self._container.exists(KEY_PATH)
                and self._container.exists(CA_CERT_PATH)
            )




