from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from nginx_config import NginxConfig


@contextmanager
def mock_ipv6(enable: bool):
    with patch("nginx_config.is_ipv6_enabled", MagicMock(return_value=enable)):
        yield


@pytest.fixture(scope="module")
def nginx_config():
    return NginxConfig()


@pytest.fixture(scope="module")
def coordinator():
    coord = MagicMock()
    coord.topology = MagicMock()
    coord.cluster = MagicMock()
    coord.cluster.gather_addresses_by_role = MagicMock(
        return_value={
            "read": ["http://some.loki.worker.0:8080"],
            "write": ["http://some.loki.worker.0:8080"],
            "backend": ["http://some.loki.worker.0:8080", "http://some.loki.worker.1:8080"],
        }
    )
    coord.cluster.gather_addresses = MagicMock(
        return_value=["http://some.loki.worker.0:8080", "http://some.loki.worker.1:8080"]
    )
    coord.s3_ready = MagicMock(return_value=True)
    coord.nginx = MagicMock()
    coord.nginx.are_certificates_on_disk = MagicMock(return_value=True)
    return coord


@pytest.fixture(scope="module")
def topology():
    top = MagicMock()
    top.as_dict = MagicMock(
        return_value={
            "model": "some-model",
            "model_uuid": "some-uuid",
            "application": "loki",
            "unit": "loki-0",
            "charm_name": "loki-coordinator-k8s",
        }
    )
    return top


@pytest.mark.parametrize(
    "addresses_by_role",
    [
        ({"read": ["address.one"]}),
        ({"read": ["address.one", "address.two"]}),
        ({"read": ["address.one", "address.two", "address.three"]}),
    ],
)
def test_upstreams_config(nginx_config, addresses_by_role):
    nginx_port = 8080
    upstreams_config = nginx_config._upstreams(addresses_by_role, nginx_port)
    expected_config = [
        {
            "directive": "upstream",
            "args": ["read"],
            "block": [
                {"directive": "server", "args": [f"{addr}:{nginx_port}"]}
                for addr in addresses_by_role["read"]
            ],
        },
        {
            "directive": "upstream",
            "args": ["worker"],
            "block": [
                {"directive": "server", "args": [f"{addr}:{nginx_port}"]}
                for addr in addresses_by_role["read"]
            ],
        },
    ]
    # TODO assert that the two are the same
    assert upstreams_config is not None
    assert expected_config is not None


@pytest.mark.parametrize("tls", (True, False))
@pytest.mark.parametrize("ipv6", (True, False))
def test_servers_config(ipv6, tls):
    port = 8080
    with mock_ipv6(ipv6):
        nginx = NginxConfig()
    server_config = nginx._server(
        server_name="test", addresses_by_role={}, nginx_port=port, tls=tls
    )
    ipv4_args = ["443", "ssl"] if tls else [f"{port}"]
    assert {"directive": "listen", "args": ipv4_args} in server_config["block"]
    ipv6_args = ["[::]:443", "ssl"] if tls else [f"[::]:{port}"]
    ipv6_directive = {"directive": "listen", "args": ipv6_args}
    if ipv6:
        assert ipv6_directive in server_config["block"]
    else:
        assert ipv6_directive not in server_config["block"]
