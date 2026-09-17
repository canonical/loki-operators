# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import dataclasses
import json
import socket
from unittest.mock import patch

import pytest
import yaml
from charms.loki_k8s.v1.loki_push_api import (
    ALERT_RULES_ENCODINGS_KEY,
    JSON_ENCODING,
    LZMA_ENCODING,
    SUPPORTED_ALERT_RULES_ENCODINGS,
    _best_alert_rules_encoding,
    _encode_alert_rules,
)
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


COMPRESSED_ALERT_RULES_RELATION = Relation(
    "logging",
    remote_app_name="app-compressed",
    remote_app_data={
        "alert_rules": _encode_alert_rules(
            json.loads(_alert_rules("compressed-group")), LZMA_ENCODING
        ),
        "metadata": _metadata("app-compressed"),
    },
)


def test_alerts_decodes_lzma_compressed_payload(
    context, s3, all_worker, nginx_prometheus_exporter_container
):
    # GIVEN a relation whose alert_rules payload is LZMA-compressed
    nginx_container = _nginx_container_with_lokitool_sync(_rule_path("app-compressed"))
    state_in = State(
        relations=[s3, all_worker, COMPRESSED_ALERT_RULES_RELATION],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the relation changed event is processed
    state_out = context.run(
        context.on.relation_changed(COMPRESSED_ALERT_RULES_RELATION), state_in
    )

    # THEN the compressed rules are decoded and written, and the unit remains active
    assert _written_group_names(context, state_out) == {"compressed-group"}
    assert isinstance(state_out.unit_status, ActiveStatus)


def test_alerts_skips_corrupt_alert_rules_and_logs_error(
    context, s3, all_worker, nginx_prometheus_exporter_container, caplog
):
    # GIVEN a relation with a corrupt/garbage alert_rules value
    corrupt_relation = Relation(
        "logging",
        remote_app_name="app-corrupt",
        remote_app_data={
            "alert_rules": "not valid json, nor valid lzma/base64",
            "metadata": _metadata("app-corrupt"),
        },
    )
    nginx_container = _nginx_container_with_lokitool_sync()
    state_in = State(
        relations=[s3, all_worker, corrupt_relation],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the relation changed event is processed
    # THEN it must not raise, and no rules are written
    state_out = context.run(context.on.relation_changed(corrupt_relation), state_in)
    assert _written_group_names(context, state_out) == set()
    assert "Could not read the alert rules published over relation" in caplog.text


def test_alerts_skips_unreadable_relation_but_returns_others(
    context, s3, all_worker, nginx_prometheus_exporter_container, caplog
):
    """One relation with unreadable alert_rules doesn't prevent others from being read.

    Regression test for the log-aggregation change: a single malformed relation is
    collected and logged once, without affecting unrelated, healthy relations.
    """
    # GIVEN one relation with corrupt alert_rules and one with valid alert_rules
    corrupt_relation = Relation(
        "logging",
        remote_app_name="app-corrupt",
        remote_app_data={
            "alert_rules": "not valid json, nor valid lzma/base64",
            "metadata": _metadata("app-corrupt"),
        },
    )
    nginx_container = _nginx_container_with_lokitool_sync(_rule_path("app-valid"))
    state_in = State(
        relations=[s3, all_worker, corrupt_relation, VALID_RELATION],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the relation changed event is processed for the valid relation
    state_out = context.run(context.on.relation_changed(VALID_RELATION), state_in)

    # THEN the valid relation's rules are still written...
    assert _written_group_names(context, state_out) == {"valid-group"}
    assert isinstance(state_out.unit_status, ActiveStatus)
    # ...and the corrupt one is reported, not silently dropped.
    assert "Could not read the alert rules published over relation" in caplog.text


def test_alerts_skips_double_json_encoded_payload_and_logs_error(
    context, s3, all_worker, nginx_prometheus_exporter_container, caplog
):
    """A plain JSON *string* (not a compressed payload) is rejected with a clear error.

    Regression test for https://github.com/canonical/prometheus-k8s-operator/pull/864
    review feedback from @Abuelodelanada: ``json.loads('"foo"')`` returns the Python
    string ``"foo"``, which then falls into the "this must be a compressed payload"
    branch and fails to decompress. This must not raise an unhandled/opaque exception.
    """
    # GIVEN a relation whose alert_rules value is a JSON string literal
    double_encoded_relation = Relation(
        "logging",
        remote_app_name="app-double-encoded",
        remote_app_data={
            "alert_rules": json.dumps("foo"),
            "metadata": _metadata("app-double-encoded"),
        },
    )
    nginx_container = _nginx_container_with_lokitool_sync()
    state_in = State(
        relations=[s3, all_worker, double_encoded_relation],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the relation changed event is processed
    # THEN it must not raise, and no rules are written
    state_out = context.run(context.on.relation_changed(double_encoded_relation), state_in)
    assert _written_group_names(context, state_out) == set()
    assert "Could not read the alert rules published over relation" in caplog.text
    assert "Could not decompress alert rules" in caplog.text


def test_alerts_skips_non_object_payload_and_logs_error(
    context, s3, all_worker, nginx_prometheus_exporter_container, caplog
):
    """A syntactically valid JSON payload that isn't an object is rejected clearly."""
    # GIVEN a relation whose alert_rules value decodes to a JSON list, not an object
    non_object_relation = Relation(
        "logging",
        remote_app_name="app-non-object",
        remote_app_data={
            "alert_rules": json.dumps([1, 2, 3]),
            "metadata": _metadata("app-non-object"),
        },
    )
    nginx_container = _nginx_container_with_lokitool_sync()
    state_in = State(
        relations=[s3, all_worker, non_object_relation],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the relation changed event is processed
    # THEN it must not raise, and no rules are written
    state_out = context.run(context.on.relation_changed(non_object_relation), state_in)
    assert _written_group_names(context, state_out) == set()
    assert "Could not read the alert rules published over relation" in caplog.text
    assert "Alert rules must be a JSON object" in caplog.text


def test_provider_advertises_alert_rules_encodings_on_relation_joined(
    context, s3, all_worker, nginx_prometheus_exporter_container
):
    # GIVEN a fresh logging relation with no rules yet
    logging_relation = Relation("logging", remote_app_name="app-fresh")
    nginx_container = _nginx_container_with_lokitool_sync()
    state_in = State(
        relations=[s3, all_worker, logging_relation],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the relation joined event is processed
    state_out = context.run(context.on.relation_joined(logging_relation), state_in)

    # THEN the provider advertises the supported alert rules encodings
    relation = state_out.get_relation(logging_relation.id)
    advertised = relation.local_app_data[ALERT_RULES_ENCODINGS_KEY]
    assert json.loads(advertised) == list(SUPPORTED_ALERT_RULES_ENCODINGS)


def test_provider_advertises_alert_rules_encodings_on_relation_changed(
    context, s3, all_worker, nginx_prometheus_exporter_container
):
    # GIVEN a relation already carrying valid rules
    nginx_container = _nginx_container_with_lokitool_sync(_rule_path("app-valid"))
    state_in = State(
        relations=[s3, all_worker, VALID_RELATION],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the relation changed event is processed
    state_out = context.run(context.on.relation_changed(VALID_RELATION), state_in)

    # THEN the provider (re)advertises the supported alert rules encodings
    relation = state_out.get_relation(VALID_RELATION.id)
    advertised = relation.local_app_data[ALERT_RULES_ENCODINGS_KEY]
    assert json.loads(advertised) == list(SUPPORTED_ALERT_RULES_ENCODINGS)


def test_provider_advertises_alert_rules_encodings_on_leader_elected(
    context, s3, all_worker, nginx_prometheus_exporter_container
):
    # GIVEN a fresh logging relation and this unit just became leader
    logging_relation = Relation("logging", remote_app_name="app-fresh")
    nginx_container = _nginx_container_with_lokitool_sync()
    state_in = State(
        relations=[s3, all_worker, logging_relation],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the leader elected event is processed
    state_out = context.run(context.on.leader_elected(), state_in)

    # THEN the provider advertises the supported alert rules encodings
    relation = state_out.get_relation(logging_relation.id)
    advertised = relation.local_app_data[ALERT_RULES_ENCODINGS_KEY]
    assert json.loads(advertised) == list(SUPPORTED_ALERT_RULES_ENCODINGS)


def test_provider_advertises_alert_rules_encodings_on_upgrade_charm(
    context, s3, all_worker, nginx_prometheus_exporter_container
):
    """The provider (re)advertises supported alert rules encodings on upgrade-charm.

    Unlike `prometheus_remote_write`'s `MetricsEndpointProvider` (which has no
    equivalent lifecycle wiring and had to gain a brand new `upgrade_charm` observer
    for this), this is already covered here for free by the existing
    `_on_lifecycle_event` handler, which every relation already runs through on
    `upgrade_charm` and calls `_publish_alert_rules_encodings` as part of
    `_process_logging_relation_changed`. This test pins that behavior down
    explicitly, so a future refactor of the lifecycle-event plumbing doesn't
    silently drop it.
    """
    # GIVEN an existing logging relation
    logging_relation = Relation("logging", remote_app_name="app-fresh")
    nginx_container = _nginx_container_with_lokitool_sync()
    state_in = State(
        relations=[s3, all_worker, logging_relation],
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )

    # WHEN the charm is upgraded
    state_out = context.run(context.on.upgrade_charm(), state_in)

    # THEN the provider (re)advertises the supported alert rules encodings
    relation = state_out.get_relation(logging_relation.id)
    advertised = relation.local_app_data[ALERT_RULES_ENCODINGS_KEY]
    assert json.loads(advertised) == list(SUPPORTED_ALERT_RULES_ENCODINGS)


def test_encode_alert_rules_json_default():
    """Default encoding is plain, sorted-keys JSON (legacy-compatible)."""
    rules = json.loads(_alert_rules("encode-test"))
    encoded = _encode_alert_rules(rules, JSON_ENCODING)
    assert json.loads(encoded) == rules
    # Not compressed: readable directly as JSON.
    assert encoded.startswith("{")


def test_unknown_encoding_falls_back_to_json():
    """An encoding this library doesn't know about is treated as plain JSON."""
    rules = json.loads(_alert_rules("unknown-encoding-test"))
    encoded = _encode_alert_rules(rules, "brotli")
    assert json.loads(encoded) == rules


@pytest.mark.parametrize("encoding", SUPPORTED_ALERT_RULES_ENCODINGS)
def test_encoding_is_deterministic(encoding):
    """The same rules, with keys in a different order, encode to identical bytes.

    Juju compares relation-databag values byte for byte to decide whether to emit
    relation-changed; an unstable key order would trigger spurious relation-changed
    events on every hook.
    """
    rules = json.loads(_alert_rules("determinism-test"))
    reordered = json.loads(json.dumps(rules))
    rule = reordered["groups"][0]["rules"][0]
    reordered["groups"][0]["rules"][0] = dict(reversed(list(rule.items())))
    assert list(reordered["groups"][0]["rules"][0]) != list(rules["groups"][0]["rules"][0])

    assert _encode_alert_rules(reordered, encoding) == _encode_alert_rules(rules, encoding)


@pytest.mark.parametrize(
    "remote_app_databag, expected",
    [
        pytest.param(None, JSON_ENCODING, id="unreadable_databag"),
        pytest.param({}, JSON_ENCODING, id="no_advertisement"),
        pytest.param({ALERT_RULES_ENCODINGS_KEY: "[]"}, JSON_ENCODING, id="nothing_advertised"),
        pytest.param(
            {ALERT_RULES_ENCODINGS_KEY: json.dumps([JSON_ENCODING])},
            JSON_ENCODING,
            id="json_only",
        ),
        pytest.param(
            {ALERT_RULES_ENCODINGS_KEY: json.dumps(["brotli"])},
            JSON_ENCODING,
            id="unknown_encoding",
        ),
        pytest.param(
            {ALERT_RULES_ENCODINGS_KEY: "not json"},
            JSON_ENCODING,
            id="malformed_advertisement",
        ),
        pytest.param(
            {ALERT_RULES_ENCODINGS_KEY: json.dumps({"lzma": True})},
            JSON_ENCODING,
            id="not_a_list",
        ),
        pytest.param(
            {ALERT_RULES_ENCODINGS_KEY: json.dumps([LZMA_ENCODING, JSON_ENCODING])},
            LZMA_ENCODING,
            id="lzma_advertised",
        ),
        pytest.param(
            {ALERT_RULES_ENCODINGS_KEY: json.dumps(["brotli", LZMA_ENCODING])},
            LZMA_ENCODING,
            id="lzma_among_unknown_encodings",
        ),
    ],
)
def test_encoding_negotiation(remote_app_databag, expected):
    """Exhaustive matrix for `_best_alert_rules_encoding`, direct against the pure function."""
    assert _best_alert_rules_encoding(remote_app_databag) == expected
