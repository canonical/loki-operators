import json
import socket
from unittest.mock import MagicMock, PropertyMock, patch

import pytest as pytest
from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer
from coordinated_workers.coordinator import Coordinator
from helpers import get_worker_config
from scenario import Container, Exec, Relation, State

from src.loki_config import (
    LOKI_ROLES_CONFIG,
    MINIMAL_DEPLOYMENT,
    RECOMMENDED_DEPLOYMENT,
)


@patch("coordinated_workers.coordinator.Coordinator.__init__", return_value=None)
@pytest.mark.parametrize(
    "roles, expected",
    (
        ({"querier": 1}, False),
        ({"distributor": 1}, False),
        ({"distributor": 1, "ingester": 1}, False),
        (dict.fromkeys(MINIMAL_DEPLOYMENT, 1), True),
        (RECOMMENDED_DEPLOYMENT, True),
    ),
)
def test_coherent(mock_coordinator, roles, expected):
    mc = Coordinator(None, None, "", "", 0, None, None, None)  # type: ignore
    cluster_mock = MagicMock()
    cluster_mock.gather_roles = MagicMock(return_value=roles)
    mc.cluster = cluster_mock
    mc._override_coherency_checker = None
    mc._roles_config = LOKI_ROLES_CONFIG

    assert mc.is_coherent is expected


@patch("coordinated_workers.coordinator.Coordinator.__init__", return_value=None)
@pytest.mark.parametrize(
    "roles, expected",
    (
        ({"query-frontend": 1}, False),
        ({"distributor": 1}, False),
        ({"distributor": 1, "ingester": 1}, False),
        (dict.fromkeys(MINIMAL_DEPLOYMENT, 1), False),
        (RECOMMENDED_DEPLOYMENT, True),
    ),
)
def test_recommended(mock_coordinator, roles, expected):
    mc = Coordinator(None, None, "", "", 0, None, None, None)  # type: ignore
    cluster_mock = MagicMock()
    cluster_mock.gather_roles = MagicMock(return_value=roles)
    mc.cluster = cluster_mock
    mc._override_recommended_checker = None
    mc._roles_config = LOKI_ROLES_CONFIG

    assert mc.is_recommended is expected

@pytest.mark.parametrize(
    "set_config",
    [
        True,
        False
    ]
)
def test_reporting_config(context, s3, all_worker, nginx_container, nginx_prometheus_exporter_container, set_config):
    """Ensure the coordinator sends the correct config for analytics and reporting to the worker."""
    # GIVEN the config for reporting in Loki Coordinator is set to a boolean
    config_value: str = set_config
    config = {"reporting_enabled": config_value}

    state_in = State(
        relations=[
            s3,
            all_worker,
        ],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
        config=config
    )

    # WHEN a worker enters a relation to a coordinator
    with context(context.on.relation_joined(all_worker), state_in) as mgr:
        state_out = mgr.run()

        # THEN the worker should have the correct boolean value for reporting in analytics
        config = get_worker_config(state_out.relations, "loki-cluster", "analytics")
        assert config["reporting_enabled"] == set_config

@pytest.mark.parametrize(
    "retention_period, expected_config",
    [
        (0, {'retention_enabled': False, 'working_directory': '/loki/compactor'}),
        (10, {'retention_enabled': True, 'working_directory': '/loki/compactor', 'delete_request_store': 's3'}),
    ]
)
def test_retention(context, s3, all_worker, nginx_container, nginx_prometheus_exporter_container, retention_period, expected_config):
    """Ensure the coordinator sends the correct config for analytics and reporting to the worker."""
    # GIVEN the config for reporting in Loki Coordinator is set to a boolean
    config_value: str = retention_period
    config = {"retention-period": config_value}

    state_in = State(
        relations=[
            s3,
            all_worker,
        ],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
        config=config
    )

    # WHEN a worker enters a relation to a coordinator
    with context(context.on.relation_joined(all_worker), state_in) as mgr:
        state_out = mgr.run()

        # THEN the worker should correctly enable/disable retention
        config = get_worker_config(state_out.relations, "loki-cluster", "compactor")
        assert config == expected_config


def test_logging_endpoint_uses_internal_url_without_ingress(
    context,
    s3,
    all_worker,
    nginx_container,
    nginx_prometheus_exporter_container,
):
    """Test that the logging endpoint uses the internal URL when ingress is not available."""
    # GIVEN a logging consumer is related to Loki without any ingress
    logging_rel = Relation("logging")

    state_in = State(
        relations=[s3, all_worker, logging_rel],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the logging relation changes
    state_out = context.run(context.on.relation_changed(logging_rel), state_in)

    # THEN the endpoint published in the logging relation data uses the internal URL
    logging_out = state_out.get_relation(logging_rel.id)
    endpoint = json.loads(logging_out.local_unit_data["endpoint"])
    expected_url = f"http://{socket.getfqdn()}:8080/loki/api/v1/push"
    assert endpoint["url"] == expected_url


def test_logging_endpoint_uses_external_url_with_ingress(
    context,
    s3,
    all_worker,
    nginx_prometheus_exporter_container,
):
    """Test that the logging endpoint uses the ingress URL when ingress is available.

    This is the fix for the bug where the logging relation endpoint always rendered
    http with socket.getfqdn() instead of https and the external_url when ingress
    (e.g. Traefik) is configured.
    """
    # GIVEN a logging consumer is related to Loki with ingress (Traefik) available
    traefik_url = "http://10.0.0.1/test-model-loki"
    logging_rel = Relation("logging")

    nginx_with_traefik = Container(
        "nginx",
        can_connect=True,
        execs={
            Exec(
                ["lokitool", "rules", "sync", f"--address={traefik_url}", "--id=fake"],
                return_code=0,
            ),
            Exec(["update-ca-certificates", "--fresh"], return_code=0),
        },
    )

    state_in = State(
        relations=[s3, all_worker, logging_rel],
        containers=[nginx_with_traefik, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the logging relation changes and ingress is available
    with patch.object(IngressPerAppRequirer, "url", new_callable=PropertyMock, return_value=traefik_url):
        state_out = context.run(context.on.relation_changed(logging_rel), state_in)

    # THEN the endpoint published in the logging relation data uses the external (ingress) URL
    logging_out = state_out.get_relation(logging_rel.id)
    endpoint = json.loads(logging_out.local_unit_data["endpoint"])
    assert endpoint["url"] == f"{traefik_url}/loki/api/v1/push"
