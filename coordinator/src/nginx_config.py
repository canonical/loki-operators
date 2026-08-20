# Copyright 2023 Canonical
# See LICENSE file for licensing details.
"""Nginx workload."""

import logging
from typing import Dict, Final, List

from charmlibs.nginx_k8s import (
    NginxLocationConfig,
    NginxUpstream,
)
from ops import Container

from loki_config import ROLES

logger = logging.getLogger(__name__)



class NginxHelper:
    """Helper class to generate the nginx configuration."""
    port: Final[int] = 3100

    _locations_write: List[NginxLocationConfig] = [
        NginxLocationConfig(path="/loki/api/v1/push", backend="write",modifier="="),
    ]

    _locations_backend: List[NginxLocationConfig] = [
        NginxLocationConfig(path="/loki/api/v1/rules", backend="backend", modifier="^~"),
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
        upstreams = [NginxUpstream(role, self.port, address_lookup_key=role) for role in ROLES]
        # add a generic `worker` upstream that routes to all workers (address_lookup_key=None includes all)
        upstreams.append(NginxUpstream("worker", self.port, address_lookup_key=None))
        return upstreams

    def server_ports_to_locations(self) -> Dict[int, List[NginxLocationConfig]]:
        """Generate a mapping from server ports to a list of Nginx location configurations."""
        return {
            self.port: self._locations_write + self._locations_backend + self._locations_read + self._locations_worker
        }




