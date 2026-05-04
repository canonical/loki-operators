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
    get_grafana_datasources_from_client_localhost,
    get_loki_rules_from_grafana,
    get_prometheus_targets_from_client_localhost,
    get_traefik_proxied_endpoints,
    query_loki_series_from_client_localhost,
)
from jubilant import Juju
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


@pytest.mark.setup
def test_build_and_deploy(juju: Juju, coordinator_charm, cos_channel):
    """Build the charm-under-test and deploy it together with related charms."""
    charm, channel, resources = coordinator_charm
    juju.deploy(
        charm, app="loki", channel=channel, resources=resources, num_units=3, trust=True
    )
    juju.deploy("prometheus-k8s", app="prometheus", channel=cos_channel, trust=True)
    juju.deploy("loki-k8s", app="loki-mono", channel=cos_channel, trust=True)
    juju.deploy("grafana-k8s", app="grafana", channel=cos_channel, trust=True)
    juju.deploy("flog-k8s", app="flog", channel="latest/edge", trust=True)
    juju.deploy("traefik-k8s", app="traefik", channel="latest/stable", trust=True)
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

    juju.wait(
        lambda status: jubilant.all_active(
            status, "prometheus", "loki-mono", "grafana", "minio", "s3", "flog"
        ),
        timeout=1000,
    )
    juju.wait(lambda status: jubilant.all_blocked(status, "loki"), timeout=1000)


@pytest.mark.setup
def test_deploy_workers(juju: Juju, cos_channel):
    """Deploy the Loki workers."""
    juju.deploy(
        "loki-worker-k8s",
        app="worker-read",
        channel=cos_channel,
        config={"role-read": True},
        num_units=3,
        trust=True,
    )
    juju.deploy(
        "loki-worker-k8s",
        app="worker-write",
        channel=cos_channel,
        config={"role-write": True},
        num_units=3,
        trust=True,
    )
    juju.deploy(
        "loki-worker-k8s",
        app="worker-backend",
        channel=cos_channel,
        config={"role-backend": True},
        num_units=3,
        trust=True,
    )
    juju.wait(
        lambda status: jubilant.all_blocked(
            status, "worker-read", "worker-write", "worker-backend"
        ),
        timeout=1000,
    )


@pytest.mark.setup
def test_integrate(juju: Juju):
    juju.integrate("loki:s3", "s3")
    juju.integrate("loki:loki-cluster", "worker-read")
    juju.integrate("loki:loki-cluster", "worker-write")
    juju.integrate("loki:loki-cluster", "worker-backend")
    juju.integrate("loki:self-metrics-endpoint", "prometheus")
    juju.integrate("loki:grafana-dashboards-provider", "grafana")
    juju.integrate("loki:grafana-source", "grafana")
    juju.integrate("loki:logging-consumer", "loki-mono")
    juju.integrate("loki:ingress", "traefik")
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
            "worker-read",
            "worker-write",
            "worker-backend",
            "traefik",
        ),
        timeout=2000,
    )


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
def test_grafana_source(juju: Juju):
    """Test the grafana-source integration, by checking that Loki appears in the Datasources."""
    datasources = get_grafana_datasources_from_client_localhost(juju)
    loki_datasources = ["loki" in d["name"] for d in datasources]
    assert any(loki_datasources)
    assert len(loki_datasources) == 1


@retry(wait=wait_fixed(20), stop=stop_after_attempt(6))
def test_loki_rules_from_grafana(juju: Juju):
    """Test that Loki alert rules can be queried through Grafana's Prometheus API.

    This validates the nginx routing in the Loki coordinator correctly handles
    the /prometheus/api/v1/rules endpoint that Grafana uses to fetch alert rules.
    """
    result = get_loki_rules_from_grafana(juju)
    assert result["status"] == "success"


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
def test_metrics_endpoint(juju: Juju):
    """Check that Loki appears in the Prometheus Scrape Targets."""
    targets = get_prometheus_targets_from_client_localhost(juju)
    loki_targets = [
        target
        for target in targets["activeTargets"]
        if target["discoveredLabels"]["juju_charm"] == "loki-coordinator-k8s"
    ]
    assert loki_targets


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
def test_logs_in_loki(juju: Juju):
    """Check that the agent metrics appear in Loki."""
    result = query_loki_series_from_client_localhost(juju)
    assert result
    assert result["data"][0]["juju_charm"] == "flog-k8s"


def test_traefik(juju: Juju):
    """Check the ingress integration, by checking if Loki is reachable through Traefik."""
    proxied_endpoints = get_traefik_proxied_endpoints(juju)
    assert "loki" in proxied_endpoints

    response = requests.get(f"{proxied_endpoints['loki']['url']}/status")
    assert response.status_code == 200
