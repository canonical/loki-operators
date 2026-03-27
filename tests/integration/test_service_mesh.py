#!/usr/bin/env python3
# Copyright 2023 Ubuntu
# See LICENSE file for licensing details.

# pyright: reportAttributeAccessIssue=false

import logging

import jubilant
import pytest
import requests
from helpers import (
    ACCESS_KEY,
    SECRET_KEY,
    configure_minio,
    configure_s3_integrator,
    get_grafana_datasources_from_client_pod,
    get_istio_ingress_ip,
    get_prometheus_targets_from_client_pod,
    query_loki_series_from_client_pod,
    service_mesh,
)
from jubilant import Juju
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


@pytest.mark.setup
def test_build_and_deploy(juju: Juju, coordinator_charm, cos_channel, mesh_channel):
    """Build the charm-under-test and deploy it together with related charms."""
    charm, channel, resources = coordinator_charm
    juju.deploy(charm, app="loki", channel=channel, resources=resources, trust=True)
    juju.deploy("prometheus-k8s", app="prometheus", channel=cos_channel, trust=True)
    juju.deploy("loki-k8s", app="loki-mono", channel=cos_channel, trust=True)
    juju.deploy("grafana-k8s", app="grafana", channel=cos_channel, trust=True)
    juju.deploy("flog-k8s", app="flog", channel="latest/stable", trust=True)
    juju.deploy("istio-k8s", app="istio", channel=mesh_channel, trust=True)
    juju.deploy("istio-beacon-k8s", app="istio-beacon", channel=mesh_channel, trust=True)
    juju.deploy("istio-ingress-k8s", app="istio-ingress", channel=mesh_channel, trust=True)
    # Deploy and configure Minio and S3
    # Secret must be at least 8 characters: https://github.com/canonical/minio-operator/issues/137
    juju.deploy(
        "minio",
        channel="ckf-1.9/stable",
        config={"access-key": ACCESS_KEY, "secret-key": SECRET_KEY},
        trust=True,
    )
    juju.deploy("s3-integrator", app="s3", channel="latest/stable", trust=True)

    juju.wait(lambda status: jubilant.all_active(status, "minio"), timeout=1000)
    juju.wait(lambda status: jubilant.all_blocked(status, "s3"), timeout=1000)
    configure_minio(juju)
    configure_s3_integrator(juju)

    # network changes might cause momentary error states
    juju.wait(
        lambda status: jubilant.all_active(
            status,
            "prometheus",
            "loki-mono",
            "grafana",
            "minio",
            "s3",
            "flog",
            "istio",
            "istio-beacon",
            "istio-ingress",
        ),
        timeout=1000,
    )
    juju.wait(lambda status: jubilant.all_blocked(status, "loki"), timeout=1000)


@pytest.mark.setup
def test_deploy_workers(juju: Juju, worker_charm):
    """Deploy the Loki workers."""
    charm, channel, resources = worker_charm
    juju.deploy(
        charm,
        app="worker",
        channel=channel,
        resources=resources,
        config={"role-all": True},
        trust=True,
    )
    juju.wait(lambda status: jubilant.all_blocked(status, "worker"), timeout=1000)


@pytest.mark.setup
def test_integrate(juju: Juju):
    juju.integrate("loki:s3", "s3")
    juju.integrate("loki:loki-cluster", "worker")
    juju.integrate("loki:self-metrics-endpoint", "prometheus")
    juju.integrate("loki:grafana-dashboards-provider", "grafana")
    juju.integrate("loki:grafana-source", "grafana")
    juju.integrate("loki:logging-consumer", "loki-mono")
    juju.integrate("loki:ingress", "istio-ingress:ingress")
    juju.integrate("flog:log-proxy", "loki")

    juju.wait(
        lambda status: jubilant.all_active(
            status,
            "loki",
            "prometheus",
            "loki-mono",
            "grafana",
            "flog",
            "minio",
            "s3",
            "worker",
            "istio-ingress",
        ),
        timeout=1000,
    )


@pytest.mark.setup
def test_enable_service_mesh(juju: Juju):
    """Enable service mesh."""
    # This is not done in the previous step for two reasons
    # 1. Not all the apps are mesh enabled yet (for eg. minio) so we need to let the apps establish comms before we enable service mesh.
    # 2. the `service_mesh` helper also provides a way to parametrize and run existing tests with service mesh enabled.
    service_mesh(
        enable=True,
        juju=juju,
        beacon_app_name="istio-beacon",
        apps_to_be_related_with_beacon=["loki"],
    )


def test_ingress(juju: Juju):
    """Check the ingress integration, by checking if Loki is reachable through the ingress endpoint."""
    ingress_address = get_istio_ingress_ip(juju, "istio-ingress")
    proxied_endpoint = f"http://{ingress_address}/{juju.model}-loki"
    response = requests.get(f"{proxied_endpoint}/status")
    assert response.status_code == 200


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
def test_grafana_source(juju: Juju):
    """Test the grafana-source integration, by checking that Loki appears in the Datasources when mesh is enabled."""
    # Query from inside the grafana pod when service mesh is enabled
    source_pod = "grafana/0"
    datasources = get_grafana_datasources_from_client_pod(juju, source_pod)
    assert "loki" in datasources[0]["name"]


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
def test_metrics_endpoint(juju: Juju):
    """Check that Loki appears in the Prometheus Scrape Targets when mesh is enabled."""
    # Query from inside the prometheus pod when service mesh is enabled
    source_pod = "prometheus/0"
    targets = get_prometheus_targets_from_client_pod(juju, source_pod)
    loki_targets = [
        target
        for target in targets["activeTargets"]
        if target["discoveredLabels"]["juju_charm"] == "loki-coordinator-k8s"
    ]
    assert loki_targets


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
def test_logs_in_loki(juju: Juju):
    """Check that the flog logs appear in Loki when mesh is enabled."""
    # Query from worker pod when service mesh is enabled
    source_pod = "worker/0"
    result = query_loki_series_from_client_pod(juju, source_pod)
    assert result
    assert result["data"][0]["juju_charm"] == "flog-k8s"
