import pytest
import sh
from helpers import deploy_swfs
from jubilant import Juju, all_active, all_blocked


def _deploy_worker(juju: Juju, worker_charm, role: str, scale: int):
    """Deploy a worker for a specific role."""
    charm_url, channel, resources = worker_charm
    juju.deploy(
        charm_url,
        role,
        channel=channel,
        resources=resources,
        trust=True,
        config={
            "role-all": False,
            f"role-{role}": True,
        },
        num_units=scale,
    )


@pytest.mark.setup
def test_deploy_workers(juju: Juju, worker_charm):
    # GIVEN an empty model

    # WHEN deploying the workers with recommended scale
    _deploy_worker(juju, worker_charm, "read", 3)
    _deploy_worker(juju, worker_charm, "write", 3)
    _deploy_worker(juju, worker_charm, "backend", 3)

    # THEN workers will be blocked because of missing coordinator integration
    juju.wait(
        lambda status: all_blocked(status, "read", "write", "backend"),
        timeout=1000,
    )


def test_all_active_when_coordinator_and_swfs_added(juju: Juju, coordinator_charm):
    # GIVEN a model with workers

    # WHEN deploying and integrating the minimal loki cluster
    deploy_swfs(juju)

    charm_url, channel, resources = coordinator_charm
    juju.deploy(
        charm_url,
        "loki",
        channel=channel,
        resources=resources,
        trust=True,
    )
    juju.integrate("loki:s3", "swfs")
    juju.integrate("loki:loki-cluster", "read")
    juju.integrate("loki:loki-cluster", "write")
    juju.integrate("loki:loki-cluster", "backend")

    # THEN both the coordinator and the workers become active
    juju.wait(
        lambda status: all_active(status, "loki", "read", "write", "backend"),
        timeout=5000,
    )


def test_juju_doctor_probes(juju: Juju):
    # GIVEN the full model
    # THEN juju-doctor passes
    try:
        sh.uvx(
            "juju-doctor",
            "check",
            probe="file://../probes/cluster-consistency.yaml",
            model=juju.model,
        )
    except sh.ErrorReturnCode as e:
        pytest.fail(f"juju-doctor failed:\n{e.stderr.decode()}")
