#!/usr/bin/env python3
# Copyright 2024 Canonical
# See LICENSE file for licensing details.

"""Loki coordinator."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

import yaml
from cosl.coordinated_workers.coordinator import ClusterRolesConfig, Coordinator
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
COMPACTOR_DIR = os.path.join(LOKI_DIR, "compactor")
CHUNKS_DIR = os.path.join(LOKI_DIR, "chunks")
ACTIVE_INDEX_DIR = os.path.join(LOKI_DIR, "index")
CACHE_DIR = os.path.join(LOKI_DIR, "index_cache")

LOKI_ROLES_CONFIG = ClusterRolesConfig(
    roles=ROLES,
    meta_roles=META_ROLES,
    minimal_deployment=MINIMAL_DEPLOYMENT,
    recommended_deployment=RECOMMENDED_DEPLOYMENT,
)


class LokiConfig:
    """Config builder for the Loki Coordinator."""

    def __init__(
        self,
        alertmanager_urls: Set[str] = set(),
        root_data_dir: Path = Path("/data"),
        recovery_data_dir: Path = Path("/recovery-data"),
    ):
        self._alertmanager_urls = alertmanager_urls
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
            "storage_config": self._storage_config(coordinator),
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
        return {
            "path_prefix": LOKI_DIR,
            "replication_factor": (
                1 if backend_scale < REPLICATION_MIN_WORKERS else DEFAULT_REPLICATION
            ),
            "compactor_grpc_address": coordinator._external_url,
            "storage": {"s3": self._s3_storage_config(coordinator)},
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

    def _memberlist_config(
        self, cluster_label: str, worker_addresses: Tuple[str, ...]
    ) -> Dict[str, Any]:
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

        return {
            "alertmanager_url": ",".join(sorted(self._alertmanager_urls)),
            "external_url": coordinator._external_url,
            "enable_sharding": True,
            # TODO: remove these, for now trying to make it work
            # "rule_path": str(self._root_data_dir / "data-ruler"),
            # "enable_api": True,
            # "storage": {"local": {"directory": str(self._root_data_dir / "data-alerts")}},
            # "ring": {"kvstore": {"store": "memberlist"}},
        }

    def _schema_config(self) -> Dict[str, Any]:
        # Ref: https://grafana.com/docs/loki/latest/configure/examples/configuration-examples/#10-expanded-s3-snippetyaml
        return {
            "configs": [
                {
                    "from": "2024-08-06",
                    "object_store": "s3",
                    "schema": "v13",
                    "store": "tsdb",
                    "index": {"period": "24h", "prefix": "index_"},
                }
            ]
        }

    def _s3_storage_config(self, coordinator: Coordinator) -> Optional[Dict[str, Any]]:
        """Build the s3_storage_config section for Loki."""
        if not coordinator.s3_ready:
            return None

        access_key = coordinator._s3_config["access_key_id"]
        secret_access_key = coordinator._s3_config["secret_access_key"]
        endpoint = coordinator._s3_config["endpoint"]
        bucket_name = coordinator._s3_config["bucket_name"]
        insecure = coordinator._s3_config["insecure"]
        region = coordinator._s3_config["region"]

        s3_storage_config = {
            "bucketnames": bucket_name,
            "endpoint": endpoint,
            "region": region,
            "access_key_id": access_key,
            "secret_access_key": secret_access_key,
            "insecure": insecure,
            "http_config": {
                "idle_conn_timeout": "90s",
                "response_header_timeout": "0s",
                "insecure_skip_verify": False,
            },
            "s3forcepathstyle": True,
        }

        return s3_storage_config

    def _storage_config(self, coordinator: Coordinator) -> Dict[str, Any]:
        # Ref: https://grafana.com/docs/loki/latest/configure/examples/configuration-examples/#2-s3-cluster-exampleyaml
        storage_config: Dict[str, Any] = {
            "tsdb_shipper": {
                "active_index_directory": ACTIVE_INDEX_DIR,
                "cache_location": CACHE_DIR,
            }
        }

        # Ref: https://grafana.com/docs/loki/latest/configure/examples/configuration-examples/#10-expanded-s3-snippetyaml
        if coordinator.s3_ready:
            # The storage_config block configures one of many possible stores for both the index
            # and chunks. Which configuration to be picked should be defined in schema_config block.
            storage_config["aws"] = self._s3_storage_config(coordinator)

        return storage_config

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
