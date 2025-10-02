from unittest.mock import MagicMock, patch

import pytest as pytest
from coordinated_workers.coordinator import Coordinator
from helpers import get_worker_config
from scenario import State

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
