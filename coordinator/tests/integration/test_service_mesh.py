#!/usr/bin/env python3
# Copyright 2023 Ubuntu
# See LICENSE file for licensing details.

# pyright: reportAttributeAccessIssue=false

import asyncio
import logging
import os
from pathlib import Path

import pytest
import requests
from helpers import (
    ACCESS_KEY,
    SECRET_KEY,
    charm_resources,
    configure_minio,
    configure_s3_integrator,
    get_grafana_datasources_from_client_pod,
    get_istio_ingress_ip,
    get_prometheus_targets_from_client_pod,
    query_loki_series_from_client_pod,
    service_mesh,
)
from pytest_operator.plugin import OpsTest
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


@pytest.mark.setup
@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest, loki_charm: str, cos_channel, mesh_channel):
    """Build the charm-under-test and deploy it together with related charms."""
    assert ops_test.model is not None  # for pyright
    await asyncio.gather(
        ops_test.model.deploy(loki_charm, "loki", resources=charm_resources(), trust=True),
        ops_test.model.deploy("prometheus-k8s", "prometheus", channel=cos_channel, trust=True),
        ops_test.model.deploy("loki-k8s", "loki-mono", channel=cos_channel, trust=True),
        ops_test.model.deploy("grafana-k8s", "grafana", channel=cos_channel, trust=True),
        ops_test.model.deploy("flog-k8s", "flog", channel="latest/stable", trust=True),
        ops_test.model.deploy("istio-k8s", "istio", channel=mesh_channel, trust=True),
        ops_test.model.deploy("istio-beacon-k8s", "istio-beacon", channel=mesh_channel, trust=True),
        ops_test.model.deploy("istio-ingress-k8s", "istio-ingress", channel=mesh_channel, trust=True),
        # Deploy and configure Minio and S3
        # Secret must be at least 8 characters: https://github.com/canonical/minio-operator/issues/137
        ops_test.model.deploy(
            "minio",
            channel="ckf-1.9/stable",
            config={"access-key": ACCESS_KEY, "secret-key": SECRET_KEY},
            trust=True,
        ),
        ops_test.model.deploy("s3-integrator", "s3", channel="latest/stable", trust=True),
    )
    await ops_test.model.wait_for_idle(apps=["minio"], status="active")
    await ops_test.model.wait_for_idle(apps=["s3"], status="blocked")
    await configure_minio(ops_test)
    await configure_s3_integrator(ops_test)

    await ops_test.model.wait_for_idle(
        apps=[
            "prometheus",
            "loki-mono",
            "grafana",
            "minio",
            "s3",
            "flog",
            "istio",
            "istio-beacon",
            "istio-ingress",
        ],
        status="active",
        timeout=1000,
        raise_on_error=False,  # network changes might cause mometary error states
    )
    await ops_test.model.wait_for_idle(apps=["loki"], status="blocked")


@pytest.mark.setup
@pytest.mark.abort_on_fail
async def test_deploy_workers(ops_test: OpsTest, cos_channel):
    """Deploy the Loki workers."""
    assert ops_test.model is not None
    # Use local worker charm if env variable is set, otherwise use charmhub
    if worker_charm := os.environ.get("WORKER_CHARM_PATH"):
        worker_resources = {"loki-image": "docker.io/ubuntu/loki:3-22.04"}
        await ops_test.model.deploy(
            Path(worker_charm),
            "worker",
            resources=worker_resources,
            config={"role-all": True},
            trust=True,
        )
    else:
        await ops_test.model.deploy(
            "loki-worker-k8s",
            "worker",
            channel=cos_channel,
            config={"role-all": True},
            trust=True,
        )
    await ops_test.model.wait_for_idle(apps=["worker"], status="blocked", raise_on_error=False)


@pytest.mark.setup
@pytest.mark.abort_on_fail
async def test_integrate(ops_test: OpsTest):
    assert ops_test.model is not None
    await asyncio.gather(
        ops_test.model.integrate("loki:s3", "s3"),
        ops_test.model.integrate("loki:loki-cluster", "worker"),
        ops_test.model.integrate("loki:self-metrics-endpoint", "prometheus"),
        ops_test.model.integrate("loki:grafana-dashboards-provider", "grafana"),
        ops_test.model.integrate("loki:grafana-source", "grafana"),
        ops_test.model.integrate("loki:logging-consumer", "loki-mono"),
        # ops_test.model.integrate("loki:ingress", "traefik"),
        ops_test.model.integrate("loki:ingress", "istio-ingress:ingress"),
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
            "worker",
            # "traefik",
            "istio-ingress"
        ],
        status="active",
        timeout=1000,
        idle_period=30,
        raise_on_error=False,
    )


@pytest.mark.setup
@pytest.mark.abort_on_fail
async def test_enable_service_mesh(ops_test: OpsTest):
    """Enable service mesh."""
    # This is not done in the previous step for two reasons
    # 1. Not all the apps are mesh enabled yet (for eg. minio) so we need to let the apps establish comms before we enable service mesh.
    # 2. the `service_mesh` helper also provides a way to parametrize and run existing tests with service mesh enabled.
    await service_mesh(
        enable=True,
        ops_test=ops_test,
        beacon_app_name="istio-beacon",
        apps_to_be_related_with_beacon=["loki"],
    )


async def test_ingress(ops_test: OpsTest):
    """Check the ingress integration, by checking if Loki is reachable through the ingress endpoint."""
    assert ops_test.model is not None
    ingress_address = get_istio_ingress_ip(ops_test, "istio-ingress")
    proxied_endpoint = f"http://{ingress_address}/{ops_test.model.name}-loki"
    response = requests.get(f"{proxied_endpoint}/status")
    assert response.status_code == 200


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
async def test_grafana_source(ops_test: OpsTest):
    """Test the grafana-source integration, by checking that Loki appears in the Datasources when mesh is enabled."""
    assert ops_test.model is not None
    # Query from inside the grafana pod when service mesh is enabled
    source_pod = "grafana/0"
    datasources = await get_grafana_datasources_from_client_pod(ops_test, source_pod)
    assert "loki" in datasources[0]["name"]


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
async def test_metrics_endpoint(ops_test: OpsTest):
    """Check that Loki appears in the Prometheus Scrape Targets when mesh is enabled."""
    assert ops_test.model is not None
    # Query from inside the prometheus pod when service mesh is enabled
    source_pod = "prometheus/0"
    targets = await get_prometheus_targets_from_client_pod(ops_test, source_pod)
    loki_targets = [
        target
        for target in targets["activeTargets"]
        if target["discoveredLabels"]["juju_charm"] == "loki-coordinator-k8s"
    ]
    assert loki_targets


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
async def test_logs_in_loki(ops_test: OpsTest):
    """Check that the flog logs appear in Loki when mesh is enabled."""
    assert ops_test.model is not None
    # Query from worker pod when service mesh is enabled
    source_pod = "worker/0"
    result = await query_loki_series_from_client_pod(ops_test, source_pod)
    assert result
    assert result["data"][0]["juju_charm"] == "flog-k8s"
