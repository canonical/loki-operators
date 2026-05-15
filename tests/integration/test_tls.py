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
from helpers import (
    ACCESS_KEY,
    SECRET_KEY,
    configure_minio,
    configure_s3_integrator,
    query_loki_series_from_client_localhost,
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
    # Deploy and configure Minio and S3
    # Secret must be at least 8 characters: https://github.com/canonical/minio-operator/issues/137
    juju.deploy(
        "minio",
        channel="ckf-1.9/stable",
        config={"access-key": ACCESS_KEY, "secret-key": SECRET_KEY},
        trust=True,
    )
    juju.deploy("s3-integrator", app="s3", channel="latest/stable", trust=True)
    # Deploy self-signed-certificates to provide TLS
    juju.deploy("self-signed-certificates", app="ca", channel="1/stable", trust=True)

    juju.wait(lambda status: jubilant.all_active(status, "minio", "ca"), timeout=1000)
    juju.wait(lambda status: jubilant.all_blocked(status, "s3"), timeout=1000)
    configure_minio(juju)
    configure_s3_integrator(juju)

    juju.wait(
        lambda status: jubilant.all_active(status, "minio", "s3", "flog", "ca"),
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
    juju.integrate("loki:s3", "s3")
    juju.integrate("loki:loki-cluster", "worker")
    juju.integrate("loki:certificates", "ca")
    juju.integrate("flog:log-proxy", "loki")

    juju.wait(
        lambda status: jubilant.all_active(
            status,
            "loki",
            "flog",
            "minio",
            "s3",
            "worker",
            "ca",
        ),
        timeout=1000,
    )


def test_worker_has_tls_config(juju: Juju):
    """Verify that the worker has TLS configuration after integrating with certificates."""
    # Check that the worker config contains TLS settings
    # The worker config is at /etc/worker/config.yaml
    task = juju.exec("cat /etc/worker/config.yaml", unit="worker/0")
    config = yaml.safe_load(task.stdout)

    # Verify server section has TLS config
    assert "server" in config, "Server section missing from worker config"
    server_config = config["server"]
    assert "http_tls_config" in server_config, "http_tls_config missing from server config"
    assert (
        "cert_file" in server_config["http_tls_config"]
    ), "cert_file missing from http_tls_config"
    assert "key_file" in server_config["http_tls_config"], "key_file missing from http_tls_config"


@retry(wait=wait_fixed(10), stop=stop_after_attempt(6))
def test_logs_in_loki_with_tls(juju: Juju):
    """Check that logs can be ingested and queried with TLS enabled."""
    result = query_loki_series_from_client_localhost(juju)
    assert result
    assert result["data"][0]["juju_charm"] == "flog-k8s"
