#!/usr/bin/env python3
# Copyright 2023 Canonical
# See LICENSE file for licensing details.

"""Loki coordinator."""

import logging
from collections import Counter
from typing import Any, Dict, Iterable, Optional, Set

import ops
from charms.alertmanager_k8s.v1.alertmanager_dispatch import AlertmanagerConsumer
from config_builder import (
    ConfigBuilder,
)
from loki_cluster import (
    LokiClusterProvider,
    LokiRole,
)
from loki_config import _S3ConfigData

logger = logging.getLogger(__name__)

MINIMAL_DEPLOYMENT = {
    LokiRole.read: 1,
    LokiRole.write: 1,
    LokiRole.backend: 1,
}
"""The minimal set of roles that need to be allocated for the
deployment to be considered consistent (otherwise we set blocked). On top of what loki itself lists as required,
we add alertmanager."""

RECOMMENDED_DEPLOYMENT = Counter(
    {
        LokiRole.read: 1,
        LokiRole.write: 1,
        LokiRole.backend: 1,
    }
)
"""The set of roles that need to be allocated for the
deployment to be considered robust according to the official recommendations/guidelines."""

# The minimum number of workers per role to enable replication
REPLICATION_MIN_WORKERS = 3
# The default amount of replicas to set when there are enough workers per role;
# otherwise, replicas will be "disabled" by setting the amount to 1
DEFAULT_REPLICATION = 3


class LokiCoordinator:
    """Loki coordinator."""

    def __init__(
        self,
        charm: ops.CharmBase,
        cluster_provider: LokiClusterProvider,
        alertmanager_consumer: AlertmanagerConsumer,
    ):
        self._charm = charm
        self._cluster_provider = cluster_provider
        self._alertmanager_consumer = alertmanager_consumer

    def is_coherent(self) -> bool:
        """Return True if the roles list makes up a coherent loki deployment."""
        roles: Iterable[LokiRole] = self._cluster_provider.gather_roles().keys()
        return set(roles).issuperset(MINIMAL_DEPLOYMENT)

    def missing_roles(self) -> Set[LokiRole]:
        """If the coordinator is incoherent, return the roles that are missing for it to become so."""
        roles: Iterable[LokiRole] = self._cluster_provider.gather_roles().keys()
        return set(MINIMAL_DEPLOYMENT).difference(roles)

    def is_recommended(self) -> bool:
        """Return True if is a superset of the minimal deployment.

        I.E. If all required roles are assigned, and each role has the recommended amount of units.
        """
        roles: Dict[LokiRole, int] = self._cluster_provider.gather_roles()
        # python>=3.11 would support roles >= RECOMMENDED_DEPLOYMENT
        for role, min_n in RECOMMENDED_DEPLOYMENT.items():
            if roles.get(role, 0) < min_n:
                return False
        return True

    def build_config(
        self, s3_config_data: Optional[_S3ConfigData], tls_enabled: bool = False
    ) -> Dict[str, Any]:
        """Generate shared config file for loki.

        Reference: https://grafana.com/docs/loki/latest/configure/
        """
        loki_config = ConfigBuilder(
            target="all",  # FIXME: Add worker's target
            instance_addr="",  # FIXME: Add worker's address
            worker_addresses=self._cluster_provider.gather_addresses(),
            cluster_label="combine-model-and-uuid-and-app-name",
            alertmanager_url=self._alerting_config(),
            external_url="external_url",  # FIXME: Check if Loki's doc is OK. See config_builde.py
            ingestion_rate_mb=int(self._charm.config["ingestion-rate-mb"]),
            ingestion_burst_size_mb=int(self._charm.config["ingestion-burst-size-mb"]),
            retention_period=int(self._charm.config["retention-period"]),
            http_tls=tls_enabled,
            s3_config_data=s3_config_data,
        ).build()

        return loki_config

    def _alerting_config(self) -> str:
        """Construct Loki altering configuration.

        Returns:
            a string consisting of comma-separated list of Alertmanager URLs
            to send notifications to.
        """
        alerting_config = ""
        alertmanagers = self._alertmanager_consumer.get_cluster_info()

        if not alertmanagers:
            logger.debug("No alertmanagers available")
            return alerting_config

        return ",".join(alertmanagers)
