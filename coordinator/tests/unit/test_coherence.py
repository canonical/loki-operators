from unittest.mock import MagicMock

import pytest as pytest
from loki_coordinator import (
    MINIMAL_DEPLOYMENT,
    RECOMMENDED_DEPLOYMENT,
    LokiCoordinator,
    LokiRole,
)


def _to_endpoint_name(role: LokiRole):
    return role.value.replace("_", "-")


ALL_MIMIR_RELATION_NAMES = list(map(_to_endpoint_name, LokiRole))


@pytest.mark.parametrize(
    "roles, expected",
    (
        ({LokiRole.read: 1}, False),
        ({LokiRole.write: 1}, False),
        ({LokiRole.backend: 1}, False),
        (MINIMAL_DEPLOYMENT, True),
        (RECOMMENDED_DEPLOYMENT, True),
    ),
)
def test_recommended(roles, expected):
    mock = MagicMock()
    mock.gather_roles = MagicMock(return_value=roles)
    lc = LokiCoordinator(mock)
    assert lc.is_recommended() is expected
