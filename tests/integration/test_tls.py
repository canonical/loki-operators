#!/usr/bin/env python3
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

# pyright: reportAttributeAccessIssue=false

"""Integration tests for TLS certificates relation.

These tests verify that the ca_cert is correctly being put into the worker config
when the coordinator is integrated with a certificates provider.
"""

import logging

import jubilant
import pytest
import yaml
import requests
from helpers import (
    deploy_swfs,
    get_unit_address,
)
from jubilant import Juju
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


@pytest.mark.setup
def test_build_and_deploy(juju: Juju, coordinator_charm, cos_channel):
    """Build the charm-under-test and deploy it together with related charms."""
    charm, channel, resources = coordinator_charm
    juju.deploy(charm, app="loki", channel=channel, resources=resources, trust=True)
    juju.deploy("flog-k8s", app="flog", channel="latest/edge", trust=True)
    deploy_swfs(juju)
    # Deploy self-signed-certificates to provide TLS
    juju.deploy("self-signed-certificates", app="ca", channel="1/stable", trust=True)

    juju.wait(lambda status: jubilant.all_active(status, "swfs", "ca"), timeout=1000)

    juju.wait(
        lambda status: jubilant.all_active(status, "swfs", "flog", "ca"),
        timeout=1000,
    )
    juju.wait(lambda status: jubilant.all_blocked(status, "loki"), timeout=1000)


@pytest.mark.setup
def test_deploy_workers(juju: Juju, cos_channel):
    """Deploy the Loki workers."""
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
    """Integrate the charms, including the certificates relation."""
    juju.integrate("loki:s3", "swfs")
    juju.integrate("loki:loki-cluster", "worker")
    juju.integrate("loki:certificates", "ca")
    juju.integrate("flog:log-proxy", "loki")

    juju.wait(
        lambda status: jubilant.all_active(
            status,
            "loki",
            "flog",
            "swfs",
            "worker",
            "ca",
        ),
        delay=3.0,
        successes=10,
        timeout=1000,
    )


def test_worker_has_tls_config(juju: Juju):
    """Verify that the worker has TLS configuration after integrating with certificates."""
    # Check that the worker config contains TLS settings
    # The worker config is at /etc/worker/config.yaml in the workload container
    output = juju.ssh("worker/0", "cat /etc/worker/config.yaml", container="loki")
    config = yaml.safe_load(output)

    # Verify server section has TLS config
    assert "server" in config, "Server section missing from worker config"
    server_config = config["server"]
    assert "http_tls_config" in server_config, (
        "http_tls_config missing from server config"
    )
    assert "cert_file" in server_config["http_tls_config"], (
        "cert_file missing from http_tls_config"
    )
    assert "key_file" in server_config["http_tls_config"], (
        "key_file missing from http_tls_config"
    )


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
def test_logs_in_loki_with_tls(juju: Juju):
    """Check that logs can be ingested and queried with TLS enabled."""
    # With TLS enabled, we must use HTTPS. We use verify=False since we're using self-signed certs.
    loki_url = get_unit_address(juju, "loki", 0)
    response = requests.get(f"https://{loki_url}:443/loki/api/v1/series", verify=False)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["data"][0]["juju_charm"] == "flog-k8s"
