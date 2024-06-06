#!/usr/bin/env python3
# Copyright 2024 Canonical
# See LICENSE file for licensing details.

"""This module contains an endpoint wrapper class for the provider side of the ``loki-cluster`` relation.

As this relation is cluster-internal and not intended for third-party charms to interact with `loki-coordinator-k8s`, its only user will be the loki-coordinator-k8s charm. As such, it does not live in a charm lib as most other relation endpoint wrappers do.
"""


import json
import logging
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Set

import ops
import pydantic
from ops import Object
from pydantic import BaseModel, ConfigDict

log = logging.getLogger("loki_cluster")

DEFAULT_ENDPOINT_NAME = "loki-cluster"
BUILTIN_JUJU_KEYS = {"ingress-address", "private-address", "egress-subnets"}
LOKI_CONFIG_FILE = "/etc/loki/loki-config.yaml"
LOKI_CERT_FILE = "/etc/loki/server.cert"
LOKI_KEY_FILE = "/etc/loki/private.key"
LOKI_CLIENT_CA_FILE = "/etc/loki/ca.cert"


class LokiRole(str, Enum):
    """Loki component role names."""

    read = "read"
    write = "write"
    backend = "backend"
    # meta roles
    all = "all"


META_ROLES = {
    LokiRole.all: (LokiRole.read, LokiRole.write, LokiRole.backend),
}


def expand_roles(roles: Iterable[LokiRole]) -> Set[LokiRole]:
    """Expand any meta roles to their 'atomic' equivalents."""
    expanded_roles = set()
    for role in roles:
        if role in META_ROLES:
            expanded_roles.update(META_ROLES[role])
        else:
            expanded_roles.add(role)
    return expanded_roles


class LokiClusterProvider(Object):
    """``loki-cluster`` provider endpoint wrapper."""

    def __init__(
        self,
        charm: ops.CharmBase,
        key: Optional[str] = None,
        endpoint: str = DEFAULT_ENDPOINT_NAME,
    ):
        super().__init__(charm, key)
        self._charm = charm
        self._relations = self.model.relations[endpoint]

    def publish_data(
        self,
        loki_config: Dict[str, Any],
        loki_endpoints: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish the loki config and loki endpoints to all related loki worker clusters."""
        for relation in self._relations:
            if relation:
                local_app_databag = LokiClusterProviderAppData(
                    loki_config=loki_config, loki_endpoints=loki_endpoints
                )
                local_app_databag.dump(relation.data[self.model.app])

    def gather_roles(self) -> Dict[LokiRole, int]:
        """Go through the worker's app databags and sum the available application roles."""
        data = {}
        for relation in self._relations:
            if relation.app:
                remote_app_databag = relation.data[relation.app]
                try:
                    worker_roles: List[LokiRole] = LokiClusterRequirerAppData.load(
                        remote_app_databag
                    ).roles
                except DataValidationError as e:
                    log.info(f"invalid databag contents: {e}")
                    worker_roles = []

                # the number of units with each role is the number of remote units
                role_n = len(relation.units)  # exclude this unit

                for role in expand_roles(worker_roles):
                    if role not in data:
                        data[role] = 0
                    data[role] += role_n
        return data

    def gather_addresses_by_role(self) -> Dict[str, Set[str]]:
        """Go through the worker's unit databags to collect all the addresses published by the units, by role."""
        data = defaultdict(set)
        for relation in self._relations:
            if not relation.app:
                log.debug(f"skipped {relation} as .app is None")
                continue

            try:
                worker_app_data = LokiClusterRequirerAppData.load(relation.data[relation.app])
                worker_roles = set(worker_app_data.roles)
            except DataValidationError as e:
                log.info(f"invalid databag contents: {e}")
                continue

            for worker_unit in relation.units:
                try:
                    worker_data = LokiClusterRequirerUnitData.load(relation.data[worker_unit])
                    unit_address = worker_data.address
                    for role in worker_roles:
                        data[role].add(unit_address)
                except DataValidationError as e:
                    log.info(f"invalid databag contents: {e}")
                    continue

        return data

    def gather_addresses(self) -> Set[str]:
        """Go through the worker's unit databags to collect all the addresses published by the units."""
        data = set()
        addresses_by_role = self.gather_addresses_by_role()
        for role, address_set in addresses_by_role.items():
            data.update(address_set)

        return data

    def get_datasource_address(self) -> Optional[str]:
        """Get datasource address."""
        addresses_by_role = self.gather_addresses_by_role()
        if address_set := addresses_by_role.get("ruler", None):
            return address_set.pop()

    def gather_topology(self) -> List[Dict[str, str]]:
        """Gather Topology."""
        data = []
        for relation in self._relations:
            if not relation.app:
                continue

            for worker_unit in relation.units:
                try:
                    worker_data = LokiClusterRequirerUnitData.load(relation.data[worker_unit])
                    unit_address = worker_data.address
                except DataValidationError as e:
                    log.info(f"invalid databag contents: {e}")
                    continue
                worker_topology = {
                    "unit": worker_unit.name,
                    "app": worker_unit.app.name,
                    "address": unit_address,
                }
                data.append(worker_topology)

        return data


class DatabagModel(BaseModel):
    """Base databag model."""

    model_config = ConfigDict(
        # Allow instantiating this class by field name (instead of forcing alias).
        populate_by_name=True,
        # Custom config key: whether to nest the whole datastructure (as json)
        # under a field or spread it out at the toplevel.
        _NEST_UNDER=None,
    )  # type: ignore
    """Pydantic config."""

    @classmethod
    def load(cls, databag: MutableMapping[str, str]):
        """Load this model from a Juju databag."""
        nest_under = cls.model_config.get("_NEST_UNDER")
        if nest_under:
            return cls.parse_obj(json.loads(databag[nest_under]))

        try:
            data = {k: json.loads(v) for k, v in databag.items() if k not in BUILTIN_JUJU_KEYS}
        except json.JSONDecodeError as e:
            msg = f"invalid databag contents: expecting json. {databag}"
            log.info(msg)
            raise DataValidationError(msg) from e

        try:
            return cls.parse_raw(json.dumps(data))  # type: ignore
        except pydantic.ValidationError as e:
            msg = f"failed to validate databag: {databag}"
            log.info(msg, exc_info=True)
            raise DataValidationError(msg) from e

    def dump(self, databag: Optional[MutableMapping[str, str]] = None, clear: bool = True):
        """Write the contents of this model to Juju databag.

        :param databag: the databag to write the data to.
        :param clear: ensure the databag is cleared before writing it.
        """
        if clear and databag:
            databag.clear()

        if databag is None:
            databag = {}
        nest_under = self.model_config.get("_NEST_UNDER")
        if nest_under:
            databag[nest_under] = self.json()

        dct = self.model_dump(by_alias=True)
        for key, field in self.model_fields.items():  # type: ignore
            value = dct[key]
            databag[field.alias or key] = json.dumps(value)
        return databag


class JujuTopology(pydantic.BaseModel):
    """JujuTopology."""

    model: str
    unit: str
    # ...


class LokiClusterProviderAppData(DatabagModel):
    """LokiClusterProviderAppData."""

    loki_config: Dict[str, Any]
    loki_endpoints: Optional[Dict[str, str]] = None
    # todo: validate with
    #  https://grafana.com/docs/loki/latest/configure/about-configurations/#:~:text=Validate%20a%20configuration,or%20in%20a%20CI%20environment.
    #  caveat: only the requirer node can do it


class LokiClusterRequirerAppData(DatabagModel):
    """LokiClusterRequirerAppData."""

    roles: List[LokiRole]


class LokiClusterRequirerUnitData(DatabagModel):
    """LokiClusterRequirerUnitData."""

    juju_topology: JujuTopology
    address: str


class LokiClusterError(Exception):
    """Base class for exceptions raised by this module."""


class DataValidationError(LokiClusterError):
    """Raised when relation databag validation fails."""


class DatabagAccessPermissionError(LokiClusterError):
    """Raised when a follower attempts to write leader settings."""
