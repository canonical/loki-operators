# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import socket
from unittest.mock import MagicMock, patch

import pytest
from charms.tempo_coordinator_k8s.v0.charm_tracing import charm_tracing_disabled
from ops import ActiveStatus
from scenario import Container, Context, Exec, Relation

from charm import LokiCoordinatorK8SOperatorCharm


@pytest.fixture(autouse=True, scope="session")
def disable_charm_tracing():
    with charm_tracing_disabled():
        yield


@pytest.fixture
def loki_charm(tmp_path):
    with patch("lightkube.core.client.GenericSyncClient"):
        with patch.multiple(
            "cosl.coordinated_workers.coordinator.KubernetesComputeResourcesPatch",
            _namespace="test-namespace",
            _patch=lambda _: None,
            get_status=lambda _: ActiveStatus(""),
            is_ready=lambda _: True,
        ):
            with patch(
                "charm.LokiCoordinatorK8SOperatorCharm._ensure_lokitool",
                MagicMock(return_value=None),
            ):
                yield LokiCoordinatorK8SOperatorCharm


@pytest.fixture(scope="function")
def context(loki_charm):
    return Context(charm_type=loki_charm)


@pytest.fixture(scope="function")
def nginx_container():
    return Container(
        "nginx",
        can_connect=True,
        execs={
            Exec(
                [
                    "lokitool",
                    "rules",
                    "sync",
                    f"--address=http://{socket.getfqdn()}:8080",
                    "--id=fake",
                ],
                return_code=0,
            )
        },
    )


@pytest.fixture(scope="function")
def nginx_prometheus_exporter_container():
    return Container(
        "nginx-prometheus-exporter",
        can_connect=True,
    )


@pytest.fixture(scope="function")
def s3_config():
    return {
        "access-key": "key",
        "bucket": "loki",
        "endpoint": "http://1.2.3.4:9000",
        "secret-key": "soverysecret",
    }


@pytest.fixture(scope="function")
def s3(s3_config):
    return Relation(
        "s3",
        remote_app_data=s3_config,
        local_unit_data={"bucket": "loki"},
    )


@pytest.fixture(scope="function")
def all_worker():
    return Relation(
        "loki-cluster",
        remote_app_data={"role": '"all"'},
        remote_units_data={
            0: {
                "address": json.dumps("localhost"),
                "juju_topology": json.dumps(
                    {"application": "worker", "unit": "worker/0", "charm_name": "loki"}
                ),
            }
        },
    )
