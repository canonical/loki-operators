from contextlib import contextmanager
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from cosl.coordinated_workers.nginx import NginxConfig

from nginx_config import (
    NginxHelper,
)


@contextmanager
def mock_ipv6(enable: bool):
    with patch("cosl.coordinated_workers.nginx.is_ipv6_enabled", MagicMock(return_value=enable)):
        yield


@pytest.fixture(scope="module")
def nginx_config():
    def _nginx_config(tls=False, ipv6=True):
        with mock_ipv6(ipv6):
            with patch.object(NginxHelper, "_tls_available", new=PropertyMock(return_value=tls)):
                nginx_helper = NginxHelper(MagicMock())
                return NginxConfig(server_name="localhost",
                                    upstream_configs=nginx_helper.upstreams(),
                                    server_ports_to_locations=nginx_helper.server_ports_to_locations())
    return _nginx_config


@pytest.mark.parametrize(
    "addresses_by_role",
    [
        ({"read": ["address.one"]}),
        ({"read": ["address.one", "address.two"]}),
        ({"read": ["address.one", "address.two", "address.three"]}),
    ],
)
def test_upstreams_config(nginx_config, addresses_by_role):
    upstreams_config = nginx_config(tls=False).get_config(addresses_by_role, False)
    # assert read upstream block
    addresses = [address for address_list in addresses_by_role.values() for address in address_list]
    for role in addresses_by_role.keys():
        assert f"upstream {role}" in upstreams_config
    for addr in addresses:
        assert f"server {addr}:{3100}" in upstreams_config
    # assert the generic `worker` upstream block
    assert "upstream worker" in upstreams_config
    for addr in addresses:
        assert f"server {addr}:{3100}" in upstreams_config

@pytest.mark.parametrize("tls", (True, False))
@pytest.mark.parametrize("ipv6", (True, False))
def test_servers_config(ipv6, tls, nginx_config):

    server_config = nginx_config(tls=tls, ipv6=ipv6).get_config(
        {"read": ["address.one"]}, tls
    )
    ipv4_args = "443 ssl" if tls else f"{8080}"
    assert f"listen {ipv4_args}" in  server_config
    ipv6_args = "[::]:443 ssl" if tls else f"[::]:{8080}"
    if ipv6:
        assert f"listen {ipv6_args}" in server_config
    else:
        assert f"listen {ipv6_args}" not in server_config
