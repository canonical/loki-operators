# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
import json

from ops.testing import Relation, State


def test_logs_to_traces_config_no_datasources(
    context,
    s3,
    all_worker,
    nginx_container,
    nginx_prometheus_exporter_container,
):
    # GIVEN no datasources exchange relations
    relations = [
        s3,
        all_worker,
    ]
    state_in = State(
        relations=relations,
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )
    # WHEN we run any event
    with context(context.on.update_status(), state_in) as mgr:
        mgr.run()
        charm = mgr.charm
        config = charm._build_logs_to_traces_config()
        # THEN derivedFields config is not generated
        assert "derivedFields" not in (config or {})


def test_logs_to_traces_config_non_tempo_datasources(
    context,
    s3,
    all_worker,
    nginx_container,
    nginx_prometheus_exporter_container,
):
    # GIVEN datasources exchange relations only with non-tempo types
    relations = [
        s3,
        all_worker,
        Relation(
            "send-datasource",
            remote_app_data={"datasources": json.dumps([{"type": "prometheus", "uid": "prometheus_1", "grafana_uid": "graf_1"}])},
        )
    ]
    state_in = State(
        relations=relations,
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )
    # WHEN we run any event
    with context(context.on.update_status(), state_in) as mgr:
        mgr.run()
        charm = mgr.charm
        config = charm._build_logs_to_traces_config()
        # THEN derivedFields config is not generated
        assert "derivedFields" not in (config or {})


def test_logs_to_traces_config_tempo_datasource(
    context,
    s3,
    all_worker,
    nginx_container,
    nginx_prometheus_exporter_container,
):
    # GIVEN a datasource exchange relations with a tempo type
    relations = [
        s3,
        all_worker,
        Relation(
            "grafana-source",
            remote_app_name="grafana",
            remote_app_data={
                "datasource_uids": json.dumps({"loki/0": "1234"}),
                "grafana_uid": "graf_1",
            },
        ),
        Relation(
            "send-datasource",
            remote_app_name="tempo",
            remote_app_data={"datasources": json.dumps([{"type": "tempo", "uid": "tempo_1", "grafana_uid": "graf_1"}])},
        ),
    ]
    state_in = State(
        relations=relations,
        containers=[nginx_container, nginx_prometheus_exporter_container],
        leader=True,
    )
    # WHEN we run any event
    with context(context.on.update_status(), state_in) as mgr:
        mgr.run()
        charm = mgr.charm
        config = charm._build_logs_to_traces_config()
        # THEN derivedFields config is generated
        assert "derivedFields" in config
        # AND it contains the remote tempo datasource uid
        assert config["derivedFields"]
        assert config["derivedFields"][0]["datasourceUid"] == "tempo_1"
