from itertools import chain

import ops
import pytest
from loki_cluster import (
    LokiClusterProvider,
    LokiClusterRequirerAppData,
    LokiClusterRequirerUnitData,
    LokiRole,
)
from ops import Framework
from scenario import Context, Relation, State


class MyCharm(ops.CharmBase):
    META = {
        "name": "lukasz",
        "requires": {"loki-cluster-require": {"interface": "loki_cluster"}},
        "provides": {"loki-cluster-provide": {"interface": "loki_cluster"}},
    }

    def __init__(self, framework: Framework):
        super().__init__(framework)
        self.provider = LokiClusterProvider(self, endpoint="loki-cluster-provide")


@pytest.mark.parametrize(
    "workers_roles, expected",
    (
        (
            (({LokiRole.read}, 1), ({LokiRole.read}, 1)),
            ({LokiRole.read: 2}),
        ),
        (
            (({LokiRole.write}, 1), ({LokiRole.read}, 1)),
            ({LokiRole.read: 1, LokiRole.write: 1}),
        ),
        ((({LokiRole.backend}, 2), ({LokiRole.backend}, 1)), ({LokiRole.backend: 3})),
        (
            (
                ({LokiRole.read}, 2),
                ({LokiRole.read}, 2),
                ({LokiRole.read, LokiRole.backend}, 1),
            ),
            ({LokiRole.read: 5, LokiRole.backend: 1}),
        ),
    ),
)
def test_role_collection(workers_roles, expected):
    relations = []
    for worker_roles, scale in workers_roles:
        data = LokiClusterRequirerAppData(roles=worker_roles).dump()
        relations.append(
            Relation(
                "loki-cluster-provide",
                remote_app_data=data,
                remote_units_data={i: {} for i in range(scale)},
            )
        )

    state = State(relations=relations)

    ctx = Context(MyCharm, meta=MyCharm.META)
    with ctx.manager("start", state) as mgr:
        mgr.run()
        charm: MyCharm = mgr.charm
        assert charm.provider.gather_roles() == expected


@pytest.mark.parametrize(
    "workers_addresses",
    (
        (("https://foo.com", "http://bar.org:8001"), ("https://bar.baz",)),
        (("//foo.com", "http://bar.org:8001"), ("foo.org:5000/noz",)),
        (
            ("https://foo.com:1", "http://bar.org:8001", "ohmysod"),
            ("u.buntu", "red-hat-chili-pepperz"),
            ("hoo.kah",),
        ),
    ),
)
def test_address_collection(workers_addresses):
    relations = []
    topo = {"unit": "foo/0", "model": "bar"}
    remote_app_data = LokiClusterRequirerAppData(roles=[LokiRole.read]).dump()
    for worker_addresses in workers_addresses:
        units_data = {
            i: LokiClusterRequirerUnitData(address=address, juju_topology=topo).dump()
            for i, address in enumerate(worker_addresses)
        }
        relations.append(
            Relation(
                "loki-cluster-provide",
                remote_units_data=units_data,
                remote_app_data=remote_app_data,
            )
        )

    # all unit addresses should show up
    expected = set(chain(*workers_addresses))

    state = State(relations=relations)

    ctx = Context(MyCharm, meta=MyCharm.META)
    with ctx.manager("start", state) as mgr:
        mgr.run()
        charm: MyCharm = mgr.charm
        assert charm.provider.gather_addresses() == expected
