# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import socket
from unittest.mock import patch

import pytest
from cosl.types import OfficialRuleFileFormat
from helpers import _written_group_names
from scenario import Container, Exec, Relation, State

from charm import NGINX_PORT, NGINX_TLS_PORT

VALID_EXPR = 'sum(rate({job="valid"}[5m])) > 0'
INVALID_EXPR = 'sum(rate({job="invalid"}[5m])) > INVALID'

VALID_LOGGING_RELATION = Relation(
    "logging",
    remote_app_name="app-valid",
    remote_app_data={
        "alert_rules": json.dumps(
            {
                "groups": [
                    {
                        "name": "valid-group",
                        "rules": [
                            {
                                "alert": "ValidRuleA",
                                "expr": 'sum(rate({job="valid"}[5m])) > 0',
                                "for": "1m",
                                "labels": {"severity": "warning"},
                                "annotations": {"summary": "valid-a"},
                            },
                        ],
                    }
                ]
            }
        ),
        "metadata": json.dumps(
            {
                "model": "test",
                "model_uuid": "20ce8299-3634-4bef-8bd8-5ace6c8816b4",
                "application": "app-valid",
                "charm_name": "app-valid-charm",
            }
        ),
    },
)

INVALID_LOGGING_RELATION = Relation(
    "logging",
    remote_app_name="app-invalid",
    remote_app_data={
        "alert_rules": json.dumps(
            {
                "groups": [
                    {
                        "name": "invalid-group",
                        "rules": [
                            {
                                "alert": "InvalidRuleA",
                                "expr": 'sum(rate({job="invalid"}[5m])) > INVALID',
                                "for": "1m",
                                "labels": {"severity": "warning"},
                                "annotations": {"summary": "invalid-a"},
                            },
                        ],
                    }
                ]
            }
        ),
        "metadata": json.dumps(
            {
                "model": "test",
                "model_uuid": "20ce8299-3634-4bef-8bd8-5ace6c8816b4",
                "application": "app-invalid",
                "charm_name": "app-invalid-charm",
            }
        ),
    },
)


@pytest.fixture
def nginx_container_with_rules():
    address_arg = f"--address=http://{socket.getfqdn()}:{NGINX_PORT}"
    address_arg_tls = f"--address=https://{socket.getfqdn()}:{NGINX_TLS_PORT}"
    return Container(
        "nginx",
        can_connect=True,
        execs={
            Exec(["lokitool", "rules", "sync"], return_code=0),
            Exec(["lokitool", "rules", "sync", address_arg, "--id=fake"], return_code=0),
            Exec(["lokitool", "rules", "sync", address_arg_tls, "--id=fake"], return_code=0),
            Exec(["update-ca-certificates", "--fresh"], return_code=0),
            Exec(["nginx", "-s", "reload"], return_code=0),
        },
    )


def _fake_validate(self, rules: OfficialRuleFileFormat, query_type=None):
    """Return an error if any rule expression contains INVALID."""
    for group in rules.get("groups", []):
        for rule in group.get("rules", []):
            if "INVALID" in rule.get("expr", ""):
                return False, f"parse error: literal not terminated in expr: {rule['expr']}"
    return True, ""


def test_valid_rules_are_written_to_disk(
    context,
    s3,
    all_worker,
    nginx_container_with_rules,
    nginx_prometheus_exporter_container,
):
    # GIVEN a logging relation with only valid alert rules
    state_in = State(
        relations=[s3, all_worker, VALID_LOGGING_RELATION],
        containers=[nginx_container_with_rules, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the logging relation changes
    with patch("cosl.cos_tool.CosTool.validate_alert_rules", _fake_validate):
        with patch(
            "charm.LokiCoordinatorK8SOperatorCharm._ensure_lokitool", return_value=None
        ):
            state_out = context.run(
                context.on.relation_changed(VALID_LOGGING_RELATION), state_in
            )

    # THEN the valid rule group is written to disk on the nginx container
    assert _written_group_names(context, state_out) == {"valid-group"}


def test_invalid_rules_are_not_written_to_disk(
    context,
    s3,
    all_worker,
    nginx_container_with_rules,
    nginx_prometheus_exporter_container,
):
    # GIVEN a logging relation where the alert rule contains an invalid expression
    state_in = State(
        relations=[s3, all_worker, INVALID_LOGGING_RELATION],
        containers=[nginx_container_with_rules, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the logging relation changes
    with patch("cosl.cos_tool.CosTool.validate_alert_rules", _fake_validate):
        with patch(
            "charm.LokiCoordinatorK8SOperatorCharm._ensure_lokitool", return_value=None
        ):
            state_out = context.run(
                context.on.relation_changed(INVALID_LOGGING_RELATION), state_in
            )

    # THEN no rule groups are written to disk
    assert _written_group_names(context, state_out) == set()


def test_only_valid_rules_written_when_mixed_relations(
    context,
    s3,
    all_worker,
    nginx_container_with_rules,
    nginx_prometheus_exporter_container,
):
    # GIVEN one logging relation with valid rules and one with invalid rules
    state_in = State(
        relations=[s3, all_worker, VALID_LOGGING_RELATION, INVALID_LOGGING_RELATION],
        containers=[nginx_container_with_rules, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the logging relation with valid rules changes
    with patch("cosl.cos_tool.CosTool.validate_alert_rules", _fake_validate):
        with patch(
            "charm.LokiCoordinatorK8SOperatorCharm._ensure_lokitool", return_value=None
        ):
            state_out = context.run(
                context.on.relation_changed(VALID_LOGGING_RELATION), state_in
            )

    # THEN only the valid group is written to disk; the invalid group is absent
    assert _written_group_names(context, state_out) == {"valid-group"}
