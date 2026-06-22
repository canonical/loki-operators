import logging

import yaml

logger = logging.getLogger(__name__)
def get_relation_data(relations, endpoint, key):
    """Retrieve the value for a given key from the local_app_data of a relation with the specified endpoint."""
    relevant = [r.local_app_data[key] for r in relations if r.endpoint == endpoint]
    assert len(relevant) < 2, "This helper currently assumes only one relation."
    return relevant[0] if relevant else None

def _written_group_names(context, state_out) -> set:
    """Return alert group names found in rendered Loki rule files."""
    fs = state_out.get_container("nginx").get_filesystem(context)
    rules_dir = fs.joinpath("etc", "loki-alerts", "rules")
    if not rules_dir.exists():
        return set()

    written_group_names = set()
    for rule_file in sorted(p for p in rules_dir.iterdir() if p.is_file()):
        written_rules = yaml.safe_load(rule_file.read_text())
        for group in written_rules["groups"]:
            written_group_names.add(group["name"])
    return written_group_names


def get_worker_config(relations, endpoint, block_key):
    relevant = [r.local_app_data for r in relations if r.endpoint == endpoint]

    assert relevant, "No matching relation found"

    # The block_key references compactor, analytics, storage, etc. Meaning the key to a section of the config
    worker_config_str = relevant[0]["worker_config"]

    worker_config = yaml.safe_load(worker_config_str)
    worker_config = yaml.safe_load(worker_config)

    # Assert the types of the parsed object
    assert isinstance(worker_config, dict)
    assert block_key in worker_config, f"Missing {block_key} in worker_config"
    assert isinstance(worker_config[block_key], dict)
    assert block_key in worker_config
    return worker_config[block_key]

