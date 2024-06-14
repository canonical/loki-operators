# Copyright 2023 Canonical
# See LICENSE file for licensing details.
"""Nginx workload."""

import logging
from typing import Any, Dict, List, Optional, Set

import crossplane
from loki_cluster import LokiClusterProvider
from ops import CharmBase
from ops.pebble import Layer

logger = logging.getLogger(__name__)


NGINX_DIR = "/etc/nginx"
NGINX_CONFIG = f"{NGINX_DIR}/nginx.conf"
NGINX_PORT = "8080"
KEY_PATH = f"{NGINX_DIR}/certs/server.key"
CERT_PATH = f"{NGINX_DIR}/certs/server.cert"
CA_CERT_PATH = f"{NGINX_DIR}/certs/ca.cert"

LOCATIONS_READ: List[Dict[str, Any]] = [
    {
        "directive": "location",
        "args": ["=", "/loki/api/v1/tail"],
        "block": [
            {
                "directive": "proxy_pass",
                "args": ["http://read"],
            },
        ],
    },
    {
        "directive": "location",
        "args": ["~", "/loki/api/.*"],
        "block": [
            {
                "directive": "proxy_pass",
                "args": ["http://read"],
            },
            {
                "directive": "proxy_set_header",
                "args": ["Upgrade $http_upgrade"],
            },
            {
                "directive": "proxy_set_header",
                "args": ['Connection "upgrade"'],
            },
        ],
    },
]

LOCATIONS_WRITE: List[Dict] = [
    {
        "directive": "location",
        "args": ["=", "/loki/api/v1/push"],
        "block": [
            {
                "directive": "proxy_pass",
                "args": ["http://write"],
            },
        ],
    },
]

# Locations shared by all the workers, regardless of the role
LOCATIONS_WORKER: List[Dict] = [
    {
        "directive": "location",
        "args": ["=", "/loki/api/v1/format_query"],
        "block": [
            {
                "directive": "proxy_pass",
                "args": ["http://worker"],
            },
        ],
    },
    {
        "directive": "location",
        "args": ["=", "/loki/api/v1/status/buildinfo"],
        "block": [
            {
                "directive": "proxy_pass",
                "args": ["http://worker"],
            },
        ],
    },
    {
        "directive": "location",
        "args": ["=", "/ring"],
        "block": [{"directive": "proxy_pass", "args": ["http://worker"]}],
    },
]

LOCATIONS_BASIC: List[Dict] = [
    {
        "directive": "location",
        "args": ["=", "/"],
        "block": [
            {"directive": "return", "args": ["200", "'OK'"]},
            {"directive": "auth_basic", "args": ["off"]},
        ],
    },
    {  # Location to be used by nginx-prometheus-exporter
        "directive": "location",
        "args": ["=", "/status"],
        "block": [
            {"directive": "stub_status", "args": []},
        ],
    },
]


class Nginx:
    """Helper class to manage the nginx workload."""

    config_path = NGINX_CONFIG

    def __init__(self, charm: CharmBase, cluster_provider: LokiClusterProvider, server_name: str):
        self._charm = charm
        self.cluster_provider = cluster_provider
        self.server_name = server_name
        self._container = self._charm.unit.get_container("nginx")

    def configure_pebble_layer(self, tls: bool) -> None:
        """Configure pebble layer."""
        if self._container.can_connect():
            self._container.push(
                self.config_path, self.config(tls=tls), make_dirs=True  # type: ignore
            )
            self._container.add_layer("nginx", self.layer, combine=True)
            self._container.autostart()

    def config(self, tls: bool = False) -> str:
        """Build and return the Nginx configuration."""
        log_level = "error"
        addresses_by_role = self.cluster_provider.gather_addresses_by_role()

        # build the complete configuration
        full_config = [
            {"directive": "worker_processes", "args": ["5"]},
            {"directive": "error_log", "args": ["/dev/stderr", log_level]},
            {"directive": "pid", "args": ["/tmp/nginx.pid"]},
            {"directive": "worker_rlimit_nofile", "args": ["8192"]},
            {
                "directive": "events",
                "args": [],
                "block": [{"directive": "worker_connections", "args": ["4096"]}],
            },
            {
                "directive": "http",
                "args": [],
                "block": [
                    # upstreams (load balancing)
                    *self._upstreams(addresses_by_role),
                    # temp paths
                    {"directive": "client_body_temp_path", "args": ["/tmp/client_temp"]},
                    {"directive": "proxy_temp_path", "args": ["/tmp/proxy_temp_path"]},
                    {"directive": "fastcgi_temp_path", "args": ["/tmp/fastcgi_temp"]},
                    {"directive": "uwsgi_temp_path", "args": ["/tmp/uwsgi_temp"]},
                    {"directive": "scgi_temp_path", "args": ["/tmp/scgi_temp"]},
                    # logging
                    {"directive": "default_type", "args": ["application/octet-stream"]},
                    {
                        "directive": "log_format",
                        "args": [
                            "main",
                            '$remote_addr - $remote_user [$time_local]  $status "$request" $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for"',
                        ],
                    },
                    *self._log_verbose(verbose=False),
                    # loki-related
                    {"directive": "sendfile", "args": ["on"]},
                    {"directive": "tcp_nopush", "args": ["on"]},
                    *self._resolver(custom_resolver=None),
                    # TODO: add custom http block for the user to config?
                    {
                        "directive": "map",
                        "args": ["$http_x_scope_orgid", "$ensured_x_scope_orgid"],
                        "block": [
                            {"directive": "default", "args": ["$http_x_scope_orgid"]},
                            {"directive": "", "args": ["anonymous"]},
                        ],
                    },
                    {"directive": "proxy_read_timeout", "args": ["300"]},
                    # server block
                    self._server(addresses_by_role, tls),
                ],
            },
        ]

        return crossplane.build(full_config)

    @property
    def layer(self) -> Layer:
        """Return the Pebble layer for Nginx."""
        return Layer(
            {
                "summary": "nginx layer",
                "description": "pebble config layer for Nginx",
                "services": {
                    "nginx": {
                        "override": "replace",
                        "summary": "nginx",
                        "command": "nginx",
                        "startup": "enabled",
                    }
                },
            }
        )

    def _log_verbose(self, verbose: bool = True) -> List[Dict[str, Any]]:
        if verbose:
            return [{"directive": "access_log", "args": ["/dev/stderr", "main"]}]
        return [
            {
                "directive": "map",
                "args": ["$status", "$loggable"],
                "block": [
                    {"directive": "~^[23]", "args": ["0"]},
                    {"directive": "default", "args": ["1"]},
                ],
            },
            {"directive": "access_log", "args": ["/dev/stderr"]},
        ]

    def _upstreams(self, addresses_by_role: Dict[str, Set[str]]) -> List[Dict[str, Any]]:
        nginx_upstreams = []
        addresses = set()
        for role, address_set in addresses_by_role.items():
            addresses = addresses.union(address_set)
            nginx_upstreams.append(
                {
                    "directive": "upstream",
                    "args": [role],
                    "block": [
                        {"directive": "server", "args": [f"{addr}:{NGINX_PORT}"]}
                        for addr in address_set
                    ],
                }
            )
        if nginx_upstreams:
            # add a generic upstream which goes to all the workers
            nginx_upstreams.append(
                {
                    "directive": "upstream",
                    "args": ["worker"],
                    "block": [
                        {"directive": "server", "args": [f"{addr}:{NGINX_PORT}"]}
                        for addr in addresses
                    ],
                }
            )

        return nginx_upstreams

    def _locations(self, addresses_by_role: Dict[str, Set[str]]) -> List[Dict[str, Any]]:
        nginx_locations = LOCATIONS_BASIC.copy()
        roles = addresses_by_role.keys()

        if "read" in roles:
            nginx_locations.extend(LOCATIONS_READ)
        if "write" in roles:
            nginx_locations.extend(LOCATIONS_WRITE)
        if roles:
            nginx_locations.extend(LOCATIONS_WORKER)
        return nginx_locations

    def _resolver(self, custom_resolver: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        if custom_resolver:
            return [{"directive": "resolver", "args": [custom_resolver]}]
        return [{"directive": "resolver", "args": ["kube-dns.kube-system.svc.cluster.local."]}]

    def _basic_auth(self, enabled: bool) -> List[Optional[Dict[str, Any]]]:
        if enabled:
            return [
                {"directive": "auth_basic", "args": ['"Loki"']},
                {
                    "directive": "auth_basic_user_file",
                    "args": ["/etc/nginx/secrets/.htpasswd"],
                },
            ]
        return []

    def _server(self, addresses_by_role: Dict[str, Set[str]], tls: bool = False) -> Dict[str, Any]:
        auth_enabled = False

        if tls:
            return {
                "directive": "server",
                "args": [],
                "block": [
                    {"directive": "listen", "args": ["443", "ssl"]},
                    {"directive": "listen", "args": ["[::]:443", "ssl"]},
                    *self._basic_auth(auth_enabled),
                    {
                        "directive": "proxy_set_header",
                        "args": ["X-Scope-OrgID", "$ensured_x_scope_orgid"],
                    },
                    # FIXME: use a suitable SERVER_NAME
                    {"directive": "server_name", "args": [self.server_name]},
                    {"directive": "ssl_certificate", "args": [CERT_PATH]},
                    {"directive": "ssl_certificate_key", "args": [KEY_PATH]},
                    {"directive": "ssl_protocols", "args": ["TLSv1", "TLSv1.1", "TLSv1.2"]},
                    {"directive": "ssl_ciphers", "args": ["HIGH:!aNULL:!MD5"]},  # pyright: ignore
                    *self._locations(addresses_by_role),
                ],
            }

        return {
            "directive": "server",
            "args": [],
            "block": [
                {"directive": "listen", "args": [NGINX_PORT]},
                {"directive": "listen", "args": [f"[::]:{NGINX_PORT}"]},
                *self._basic_auth(auth_enabled),
                {
                    "directive": "proxy_set_header",
                    "args": ["X-Scope-OrgID", "$ensured_x_scope_orgid"],
                },
                *self._locations(addresses_by_role),
            ],
        }
