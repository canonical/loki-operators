#!/usr/bin/env python3
# Copyright 2024 Canonical
# See LICENSE file for licensing details.

"""Loki coordinator."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Set

import yaml
from cosl.coordinated_workers.coordinator import Coordinator
from cosl.coordinated_workers.worker import CERT_FILE, KEY_FILE

logger = logging.getLogger(__name__)


"""Loki component role names."""
ROLES = {
    "read",
    "write",
    "backend",
    "all",
}

META_ROLES = {
    "all": set(ROLES),
}

"""The minimal set of roles that need to be allocated for the
deployment to be considered consistent (otherwise we set blocked)."""
MINIMAL_DEPLOYMENT = {
    "read",
    "write",
    "backend",
}

"""The set of roles that need to be allocated for the
deployment to be considered robust according to the official recommendations/guidelines."""
RECOMMENDED_DEPLOYMENT = {
    "read": 3,
    "write": 3,
    "backend": 3,
}

# The minimum number of workers per role to enable replication
REPLICATION_MIN_WORKERS = 3
# The default amount of replicas to set when there are enough workers per role;
# otherwise, replicas will be "disabled" by setting the amount to 1
DEFAULT_REPLICATION = 3

HTTP_LISTEN_PORT = 3100
LOKI_DIR = "/loki"
BOLTDB_DIR = os.path.join(LOKI_DIR, "boltdb-shipper-active")
BOLTDB_CACHE_DIR = os.path.join(LOKI_DIR, "boltdb-shipper-cache")
COMPACTOR_DIR = os.path.join(LOKI_DIR, "compactor")
CHUNKS_DIR = os.path.join(LOKI_DIR, "chunks")
RULES_DIR = os.path.join(LOKI_DIR, "rules")


class LokiRolesConfig:
    """Define the configuration for Loki roles.

    This object implements the ClusterRolesConfig Protocol.
    """

    roles: Iterable[str] = ROLES
    meta_roles: Mapping[str, Iterable[str]] = META_ROLES
    minimal_deployment: Iterable[str] = MINIMAL_DEPLOYMENT
    recommended_deployment: Dict[str, int] = RECOMMENDED_DEPLOYMENT


class LokiConfig:
    """Config builder for the Loki Coordinator."""

    def __init__(
        self,
        root_data_dir: Path = Path("/data"),
        recovery_data_dir: Path = Path("/recovery-data"),
    ):
        self._root_data_dir = root_data_dir
        self._recovery_data_dir = recovery_data_dir

    def config(self, coordinator: Coordinator) -> str:
        """Generate shared config file for mimir.

        Reference: https://grafana.com/docs/loki/latest/configuration/
        """
        loki_config: Dict[str, Any] = {
            "auth_enabled": False,
            "chunk_store_config": self._chunk_store_config(),
            "common": self._common_config(coordinator),
            "compactor": self._compactor_config(
                retention_period=int(coordinator._charm.config["retention-period"])
            ),
            "frontend": self._frontend_config(),
            "ingester": self._ingester_config(),
            "limits_config": self._limits_config(
                ingestion_rate_mb=int(coordinator._charm.config["ingestion-rate-mb"]),
                ingestion_burst_size_mb=int(coordinator._charm.config["ingestion-burst-size-mb"]),
                retention_period=int(coordinator._charm.config["retention-period"]),
            ),
            "memberlist": self._memberlist_config(
                cluster_label=f"{coordinator._charm.model.name}-cluster",
                worker_addresses=coordinator.cluster.gather_addresses(),
            ),
            "querier": self._querier_config(),
            "query_range": self._query_range_config(),
            "ruler": self._ruler_config(coordinator),
            "schema_config": self._schema_config(),
            "storage_config": self._storage_config(),
            "server": self._server_config(coordinator),
        }

        return yaml.dump(loki_config)

    def _chunk_store_config(self) -> Dict[str, Any]:
        # Ref: https://grafana.com/docs/loki/latest/configure/#chunk_store_config
        return {
            "chunk_cache_config": {
                "embedded_cache": {
                    # https://community.grafana.com/t/too-many-outstanding-requests-on-loki-2-7-1/78249/11
                    "enabled": True
                }
            }
        }

    def _common_config(self, coordinator: Coordinator) -> Dict[str, Any]:
        backend_scale = len(coordinator.cluster.gather_addresses_by_role().get("backend", []))
        storage = {
            "filesystem": {
                "chunks_directory": CHUNKS_DIR,
                "rules_directory": RULES_DIR,
            }
        }

        if coordinator.s3_ready:
            storage = {"s3": coordinator._s3_config}

        return {
            "path_prefix": LOKI_DIR,
            "replication_factor": (
                1 if backend_scale < REPLICATION_MIN_WORKERS else DEFAULT_REPLICATION
            ),
            "storage": storage,
        }

    def _compactor_config(self, retention_period: int) -> Dict[str, Any]:
        # Ref: https://grafana.com/docs/loki/latest/configure/#compactor
        retention_enabled = retention_period != 0
        return {
            # Activate custom retention. Default is False.
            "retention_enabled": retention_enabled,
            "working_directory": COMPACTOR_DIR,
        }

    def _frontend_config(self) -> Dict[str, Any]:
        # Ref: https://grafana.com/docs/loki/latest/configure/#frontend
        return {
            # Maximum number of outstanding requests per tenant per frontend; requests beyond this error with HTTP 429.
            # Default is 2048, but 8cpu16gb can ingest ~3 times more, so set to 4x.
            "max_outstanding_per_tenant": 8192,
            # Compress HTTP responses.
            "compress_responses": True,
        }

    def _ingester_config(self) -> Dict[str, Any]:
        return {
            "wal": {
                "dir": os.path.join(CHUNKS_DIR, "wal"),
                "enabled": True,
                "flush_on_shutdown": True,
            }
        }

    def _limits_config(
        self, ingestion_rate_mb: int, ingestion_burst_size_mb: int, retention_period: int
    ) -> Dict[str, Any]:
        # Ref: https://grafana.com/docs/loki/latest/configure/#limits_config
        return {
            # For convenience, we use an integer but Loki takes a float
            "ingestion_rate_mb": float(ingestion_rate_mb),
            "ingestion_burst_size_mb": float(ingestion_burst_size_mb),
            # The per-stream limits are intentionally set to match the per-user limits, to simplify UX and address the
            # case of one stream per user.
            "per_stream_rate_limit": f"{ingestion_rate_mb}MB",
            "per_stream_rate_limit_burst": f"{ingestion_burst_size_mb}MB",
            # This charmed operator is intended for running a single loki instances, so we don't need to split queries
            # https://community.grafana.com/t/too-many-outstanding-requests-on-loki-2-7-1/78249/9
            "split_queries_by_interval": "0",
            "retention_period": f"{retention_period}d",
        }

    def _memberlist_config(self, cluster_label: str, worker_addresses: Set[str]) -> Dict[str, Any]:
        return {
            "cluster_label": cluster_label,
            "join_members": list(worker_addresses),
        }

    def _querier_config(self) -> Dict[str, Any]:
        # Ref: https://grafana.com/docs/loki/latest/configure/#querier
        return {
            # The maximum number of concurrent queries allowed. Default is 10.
            "max_concurrent": 20,
        }

    def _query_range_config(self) -> Dict[str, Any]:
        # Ref: https://grafana.com/docs/loki/latest/configure/#query_range
        return {
            "parallelise_shardable_queries": False,
            "results_cache": {
                "cache": {
                    "embedded_cache": {
                        # https://community.grafana.com/t/too-many-outstanding-requests-on-loki-2-7-1/78249/11
                        "enabled": True
                    }
                }
            },
        }

    def _ruler_config(self, coordinator: Coordinator) -> Dict[str, Any]:
        # Reference: https://grafana.com/docs/loki/latest/configure/#ruler
        # TODO: Check if Loki documentation is ok, as it says:
        #
        # Base URL of the Grafana instance.
        # CLI flag: -ruler.external.url
        # [external_url: <url>]
        #
        # But we are setting Loki's external url

        # FIXME: Implement in Coordinator:
        # self.alertmanager_consumer = AlertmanagerConsumer(self, relation_name="alertmanager")
        #
        return {
            "alertmanager_url": "",  # self.alertmanager_url,
            "external_url": coordinator._external_url,
        }

    def _schema_config(self) -> Dict[str, Any]:
        return {
            "configs": [
                {
                    "from": "2020-10-24",
                    "index": {"period": "24h", "prefix": "index_"},
                    "object_store": "filesystem",
                    "schema": "v11",
                    "store": "boltdb-shipper",
                }
            ]
        }

    def _storage_config(self) -> Dict[str, Any]:
        # Ref: https://grafana.com/docs/loki/latest/configure/#storage_config
        return {
            "boltdb_shipper": {
                "active_index_directory": BOLTDB_DIR,
                "shared_store": "filesystem",
                "cache_location": BOLTDB_CACHE_DIR,
            },
            "filesystem": {"directory": CHUNKS_DIR},
        }

    def _server_config(self, coordinator: Coordinator) -> Dict[str, Any]:
        _server = {
            "http_listen_address": "0.0.0.0",
            "http_listen_port": HTTP_LISTEN_PORT,
        }

        if coordinator.nginx.are_certificates_on_disk:
            _server["http_tls_config"] = {
                "cert_file": CERT_FILE,  # HTTP server cert path.
                "key_file": KEY_FILE,  # HTTP server key path.
            }

        return _server
