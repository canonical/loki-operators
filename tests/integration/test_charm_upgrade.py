#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# pyright: reportAttributeAccessIssue=false

"""Upgrade integration test: deploy from edge, refresh to locally built charms."""

import logging

import jubilant
import pytest
from helpers import (
    deploy_swfs,
    query_loki_series_from_client_localhost,
)
from jubilant import Juju
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.skip(reason="Cross-base upgrade from 24.04 to 26.04 not supported")


@pytest.mark.setup
def test_deploy_from_edge(juju: Juju, cos_channel):
    """Deploy the coordinator and infrastructure from the edge channel."""
    juju.deploy("loki-coordinator-k8s", app="loki", channel=cos_channel, trust=True)
    juju.deploy("flog-k8s", app="flog", channel="latest/stable", trust=True)
    deploy_swfs(juju)

    juju.wait(
        lambda status: jubilant.all_active(status, "swfs", "flog"),
        timeout=1000,
    )
    juju.wait(lambda status: jubilant.all_blocked(status, "loki"), timeout=1000)


@pytest.mark.setup
def test_deploy_workers_from_edge(juju: Juju, cos_channel):
    """Deploy the Loki worker from the edge channel."""
    juju.deploy(
        "loki-worker-k8s",
        app="worker",
        channel=cos_channel,
        config={"role-all": True},
        trust=True,
    )
    juju.wait(lambda status: jubilant.all_blocked(status, "worker"), timeout=1000)


@pytest.mark.setup
def test_integrate(juju: Juju):
    """Set up the integrations between all applications."""
    juju.integrate("loki:s3", "swfs")
    juju.integrate("loki:loki-cluster", "worker")
    juju.integrate("flog:log-proxy", "loki")

    juju.wait(
        lambda status: jubilant.all_active(
            status, "loki", "flog", "swfs", "worker"
        ),
        timeout=1000,
    )


@pytest.mark.setup
def test_upgrade(juju: Juju, coordinator_charm, worker_charm):
    """Refresh the coordinator and worker from the locally built charms."""
    coord_charm, coord_channel, coord_resources = coordinator_charm
    if coord_channel:
        juju.refresh("loki", channel=coord_channel)
    else:
        juju.refresh("loki", path=coord_charm, resources=coord_resources)

    wkr_charm, wkr_channel, wkr_resources = worker_charm
    if wkr_channel:
        juju.refresh("worker", channel=wkr_channel)
    else:
        juju.refresh("worker", path=wkr_charm, resources=wkr_resources)

    juju.wait(
        lambda status: jubilant.all_active(
            status, "loki", "flog", "swfs", "worker"
        ),
        timeout=1000,
    )


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
def test_logs_in_loki(juju: Juju):
    """Check that flog logs appear in Loki after the upgrade."""
    result = query_loki_series_from_client_localhost(juju)
    assert result
    assert result["data"][0]["juju_charm"] == "flog-k8s"
