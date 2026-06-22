# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import dataclasses
import json
import socket
from unittest.mock import patch

import yaml
from cosl import JujuTopology
from ops.model import ActiveStatus, BlockedStatus
from scenario import Container, Exec, Relation, State

from charm import NGINX_PORT, RULES_DIR


def _alert_rules(group_name: str, valid: bool = True) -> str:
    invalid_expr = 'sum(rate({job="invalid"}[5m])) >'
    return json.dumps(
        {
            "groups": [
                {
                    "name": group_name,
                    "rules": [
                        {
                            "alert": f"{group_name}ValidA",
                            "expr": 'sum(rate({job="valid"}[5m])) > 0',
                            "for": "1m",
                            "labels": {"severity": "warning"},
                            "annotations": {"summary": "valid-a"},
                        },
                        {
                            "alert": f"{group_name}ValidB",
                            "expr": 'sum(rate({job="valid"}[10m])) > 0'
                            if valid
                            else invalid_expr,
                            "for": "1m",
                            "labels": {"severity": "warning"},
                            "annotations": {"summary": "valid-b"},
                        },
                    ],
                }
            ]
        }
    )


def _metadata(app_name: str) -> str:
    return json.dumps(
        {
            "model": "test",
            "model_uuid": "20ce8299-3634-4bef-8bd8-5ace6c8816b4",
            "application": app_name,
            "charm_name": f"{app_name}-charm",
        }
    )


def _rule_path(app_name: str) -> str:
    identifier = JujuTopology.from_dict(json.loads(_metadata(app_name))).identifier
    return f"{RULES_DIR}/juju_{identifier}.rules"


VALID_RELATION = Relation(
    "logging",
    remote_app_name="app-valid",
    remote_app_data={
        "alert_rules": _alert_rules("valid-group"),
        "metadata": _metadata("app-valid"),
    },
)

INVALID_RELATION = Relation(
    "logging",
    remote_app_name="app-invalid",
    local_app_data={"event": json.dumps({"errors": "parse error"})},
    remote_app_data={"metadata": _metadata("app-invalid")},
)

INVALID_RULES_RELATION = Relation(
    "logging",
    remote_app_name="app-invalid",
    remote_app_data={
        "alert_rules": _alert_rules("invalid-group", valid=False),
        "metadata": _metadata("app-invalid"),
    },
)


def _nginx_container_with_lokitool_sync(*rule_paths: str) -> Container:
    return Container(
        "nginx",
        can_connect=True,
        execs={
            Exec(
                [
                    "lokitool",
                    "rules",
                    "sync",
                    *rule_paths,
                    f"--address=http://{socket.getfqdn()}:{NGINX_PORT}",
                    "--id=fake",
                ],
                return_code=0,
            ),
            Exec(["update-ca-certificates", "--fresh"], return_code=0),
            Exec(["nginx", "-s", "reload"], return_code=0),
        },
    )


def _written_group_names(context, state_out):
    """Return alert group names found in rendered Loki rule files."""
    fs = state_out.get_container("nginx").get_filesystem(context)
    rules_dir = fs.joinpath("etc", "loki-alerts", "rules")
    if not rules_dir.exists():
        return set()

    written_group_names = set()
    for rule_file in sorted(path for path in rules_dir.iterdir() if path.is_file()):
        written_rules = yaml.safe_load(rule_file.read_text())
        for group in written_rules["groups"]:
            written_group_names.add(group["name"])
    return written_group_names


def _relation_errors(relation: Relation) -> str:
    event = json.loads(relation.local_app_data.get("event", "{}"))
    return event.get("errors", "")


def _validate_alert_rules(_, rules):
    group_name = rules["groups"][0]["name"]
    if "invalid" in group_name:
        return False, f"{group_name} is invalid"
    return True, ""


def test_valid_relation_only(context, s3, all_worker, nginx_prometheus_exporter_container):
    # GIVEN one relation with only valid rules
    nginx_container = _nginx_container_with_lokitool_sync(_rule_path("app-valid"))
    state_in = State(
        relations=[s3, all_worker, VALID_RELATION],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the relation changed event is processed
    state_out = context.run(context.on.relation_changed(VALID_RELATION), state_in)

    # THEN valid rules are written and unit remains active
    assert _written_group_names(context, state_out) == {"valid-group"}
    assert isinstance(state_out.unit_status, ActiveStatus)


def test_invalid_relation_only(context, s3, all_worker, nginx_prometheus_exporter_container):
    # GIVEN one relation where alert rule validation failed
    nginx_container = _nginx_container_with_lokitool_sync()
    state_in = State(
        relations=[s3, all_worker, INVALID_RELATION],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the relation changed event is processed
    state_out = context.run(context.on.relation_changed(INVALID_RELATION), state_in)

    # THEN invalid relation rules are not written and unit is blocked
    assert _written_group_names(context, state_out) == set()
    assert isinstance(state_out.unit_status, BlockedStatus)


def test_valid_and_invalid_relations(context, s3, all_worker, nginx_container, nginx_prometheus_exporter_container):
    # GIVEN one valid relation and one invalid relation
    nginx_container = _nginx_container_with_lokitool_sync(_rule_path("app-valid"))
    state_in = State(
        relations=[s3, all_worker, VALID_RELATION, INVALID_RELATION],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the relation changed event is processed
    state_out = context.run(context.on.relation_changed(VALID_RELATION), state_in)

    # THEN only valid relation rules are written and unit is blocked due to invalid relation
    assert _written_group_names(context, state_out) == {"valid-group"}
    assert isinstance(state_out.unit_status, BlockedStatus)

def test_invalid_relation_becoming_valid_recovers_to_active(
    context, s3, all_worker, nginx_prometheus_exporter_container
):
    # GIVEN a logging relation with invalid rules has already reported errors
    nginx_container = _nginx_container_with_lokitool_sync()
    state_in = State(
        leader=True,
        relations=[s3, all_worker, INVALID_RULES_RELATION],
        containers=[nginx_container, nginx_prometheus_exporter_container],
    )

    with patch(
        "charms.loki_k8s.v1.loki_push_api.CosTool.validate_alert_rules",
        autospec=True,
        side_effect=_validate_alert_rules,
    ):
        invalid_state = context.run(
            context.on.relation_changed(INVALID_RULES_RELATION), state_in
        )
        relation_after_invalid = invalid_state.get_relation(INVALID_RULES_RELATION.id)

        assert _relation_errors(relation_after_invalid)
        assert _written_group_names(context, invalid_state) == set()
        assert isinstance(invalid_state.unit_status, BlockedStatus)

        # WHEN the same logging relation updates its rules to become valid
        now_valid_relation = dataclasses.replace(
            relation_after_invalid,
            remote_app_data={
                **relation_after_invalid.remote_app_data,
                "alert_rules": VALID_RELATION.remote_app_data["alert_rules"],
            },
        )

        recovered_state = context.run(
            context.on.relation_changed(now_valid_relation),
            dataclasses.replace(
                invalid_state,
                relations=[s3, all_worker, now_valid_relation],
                containers=[
                    _nginx_container_with_lokitool_sync(_rule_path("app-invalid")),
                    nginx_prometheus_exporter_container,
                ],
            ),
        )
        recovered_relation = recovered_state.get_relation(INVALID_RULES_RELATION.id)

        # THEN the previous invalid relation error is cleared and valid rules are written
        assert not _relation_errors(recovered_relation)
        assert _written_group_names(context, recovered_state) == {"valid-group"}
        assert isinstance(recovered_state.unit_status, ActiveStatus)
