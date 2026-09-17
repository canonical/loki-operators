# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os
import subprocess
from pathlib import Path
from typing import Literal

from pytest import fixture
from pytest_jubilant import get_resources, pack

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]


@fixture(scope="session")
def cos_channel():
    return "dev/edge"


@fixture(scope="session")
def mesh_channel():
    return "2/edge"


def charm_and_channel_and_resources(
    role: Literal["coordinator", "worker"], charm_path_key: str, charm_channel_key: str
):
    """Loki coordinator or worker charm used for integration testing.

    Build once per session and reuse in all integration tests.
    """
    if channel_from_env := os.getenv(charm_channel_key):
        charm = f"loki-{role}-k8s"
        logger.info("Using published %s charm from %s", charm, channel_from_env)
        return charm, channel_from_env, None
    if path_from_env := os.getenv(charm_path_key):
        charm_path = Path(path_from_env).absolute()
        logger.info("Using local %s charm: %s", role, charm_path)
        return charm_path, None, get_resources(REPO_ROOT / role)
    for _ in range(3):
        logger.info("packing Loki %s charm...", role)
        try:
            pth = pack(REPO_ROOT / role)
        except subprocess.CalledProcessError:
            logger.warning("Failed to build Loki %s. Trying again!", role)
            continue
        pth = _resolve_packed_charm(pth, REPO_ROOT / role)
        os.environ[charm_path_key] = str(pth)
        return pth, None, get_resources(REPO_ROOT / role)
    raise subprocess.CalledProcessError(1, f"pack {role}")


def _resolve_packed_charm(packed: Path, project_dir: Path) -> Path:
    # charmcraft 4.4.1 and 4.4.2 ignore the output directory passed to
    # `charmcraft pack` and leave the .charm file inside the project
    # directory instead: https://github.com/canonical/charmcraft/issues/2854
    # Same workaround as Juju's test helpers: https://github.com/juju/juju/pull/23174
    if packed.is_file():
        return packed
    in_project_dir = project_dir / packed.name
    if in_project_dir.is_file():
        return in_project_dir
    raise FileNotFoundError(
        f"packed charm {packed.name} not found in {packed.parent} or {project_dir}"
    )


@fixture(scope="session")
def coordinator_charm():
    """Loki coordinator used for integration testing."""
    return charm_and_channel_and_resources(
        "coordinator", "COORDINATOR_CHARM_PATH", "COORDINATOR_CHARM_CHANNEL"
    )


@fixture(scope="session")
def worker_charm():
    """Loki worker used for integration testing."""
    return charm_and_channel_and_resources(
        "worker", "WORKER_CHARM_PATH", "WORKER_CHARM_CHANNEL"
    )
