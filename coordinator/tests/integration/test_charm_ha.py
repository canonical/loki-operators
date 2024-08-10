#!/usr/bin/env python3
# Copyright 2023 Ubuntu
# See LICENSE file for licensing details.

# pyright: reportAttributeAccessIssue=false

import logging

import pytest
import requests
from helpers import (
    ACCESS_KEY,
    SECRET_KEY,
    charm_resources,
    configure_minio,
    configure_s3_integrator,
    get_grafana_datasources,
    get_prometheus_targets,
    get_traefik_proxied_endpoints,
    query_loki_series,
)
from pytest_operator.plugin import OpsTest
from tenacity import retry, stop_after_attempt, wait_fixed

from tests.integration.test_charm_ha_scaled import asyncio

logger = logging.getLogger(__name__)


@pytest.mark.setup
@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest, loki_charm: str):
    """Build the charm-under-test and deploy it together with related charms."""
    assert ops_test.model is not None  # for pyright
    await asyncio.gather(
        ops_test.model.deploy(loki_charm, "loki", resources=charm_resources()),
        ops_test.model.deploy("prometheus-k8s", "prometheus", channel="latest/stable", trust=True),
        ops_test.model.deploy("loki-k8s", "loki-mono", channel="latest/stable", trust=True),
        ops_test.model.deploy("grafana-k8s", "grafana", channel="latest/stable", trust=True),
        ops_test.model.deploy("flog-k8s", "flog", channel="latest/stable", trust=True),
        ops_test.model.deploy("traefik-k8s", "traefik", channel="latest/stable", trust=True),
        # Deploy and configure Minio and S3
        # Secret must be at least 8 characters: https://github.com/canonical/minio-operator/issues/137
        ops_test.model.deploy(
            "minio",
            channel="latest/stable",
            config={"access-key": ACCESS_KEY, "secret-key": SECRET_KEY},
        ),
        ops_test.model.deploy("s3-integrator", "s3", channel="latest/stable"),
    )
    await ops_test.model.wait_for_idle(apps=["minio"], status="active")
    await ops_test.model.wait_for_idle(apps=["s3"], status="blocked")
    await configure_minio(ops_test)
    await configure_s3_integrator(ops_test)

    await ops_test.model.wait_for_idle(
        apps=["prometheus", "loki-mono", "grafana", "minio", "s3", "flog"], status="active"
    )
    await ops_test.model.wait_for_idle(apps=["loki"], status="blocked")


@pytest.mark.setup
@pytest.mark.abort_on_fail
async def test_deploy_workers(ops_test: OpsTest):
    """Deploy the Loki workers."""
    assert ops_test.model is not None
    await ops_test.model.deploy(
        "loki-worker-k8s",
        "worker-read",
        channel="latest/edge",
        config={"role-read": True},
    )
    await ops_test.model.deploy(
        "loki-worker-k8s",
        "worker-write",
        channel="latest/edge",
        config={"role-write": True},
    )
    await ops_test.model.deploy(
        "loki-worker-k8s",
        "worker-backend",
        channel="latest/edge",
        config={"role-backend": True},
    )
    await ops_test.model.wait_for_idle(
        apps=["worker-read", "worker-write", "worker-backend"], status="blocked"
    )


@pytest.mark.setup
@pytest.mark.abort_on_fail
async def test_integrate(ops_test: OpsTest):
    assert ops_test.model is not None
    await asyncio.gather(
        ops_test.model.integrate("loki:s3", "s3"),
        ops_test.model.integrate("loki:loki-cluster", "worker-read"),
        ops_test.model.integrate("loki:loki-cluster", "worker-write"),
        ops_test.model.integrate("loki:loki-cluster", "worker-backend"),
        ops_test.model.integrate("loki:self-metrics-endpoint", "prometheus"),
        ops_test.model.integrate("loki:grafana-dashboards-provider", "grafana"),
        ops_test.model.integrate("loki:grafana-source", "grafana"),
        ops_test.model.integrate("loki:logging-consumer", "loki-mono"),
        ops_test.model.integrate("loki:ingress", "traefik"),
        ops_test.model.integrate("flog:log-proxy", "loki"),
    )

    await ops_test.model.wait_for_idle(
        apps=[
            "loki",
            "prometheus",
            "loki-mono",
            "grafana",
            "flog",
            "minio",
            "s3",
            "traefik",
            "worker-read",
            "worker-write",
            "worker-backend",
        ],
        status="active",
    )


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
async def test_grafana_source(ops_test: OpsTest):
    """Test the grafana-source integration, by checking that Loki appears in the Datasources."""
    assert ops_test.model is not None
    datasources = await get_grafana_datasources(ops_test)
    assert "loki" in datasources[0]["name"]


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
async def test_metrics_endpoint(ops_test: OpsTest):
    """Check that Loki appears in the Prometheus Scrape Targets."""
    assert ops_test.model is not None
    targets = await get_prometheus_targets(ops_test)
    loki_targets = [
        target
        for target in targets["activeTargets"]
        if target["discoveredLabels"]["juju_charm"] == "loki-coordinator-k8s"
    ]
    assert loki_targets


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
async def test_logs_in_loki(ops_test: OpsTest):
    """Check that the agent metrics appear in Loki."""
    result = await query_loki_series(ops_test)
    assert result
    assert result["data"][0]["juju_charm"] == "flog-k8s"


async def test_traefik(ops_test: OpsTest):
    """Check the ingress integration, by checking if Loki is reachable through Traefik."""
    assert ops_test.model is not None
    proxied_endpoints = await get_traefik_proxied_endpoints(ops_test)
    assert "loki" in proxied_endpoints

    response = requests.get(f"{proxied_endpoints['loki']['url']}/status")
    assert response.status_code == 200
