import json
import logging
from typing import Any, Dict, List

import requests
import yaml
from juju.application import Application
from juju.unit import Unit
from lightkube import Client
from lightkube.generic_resource import create_namespaced_resource
from minio import Minio
from pytest_operator.plugin import OpsTest
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

ACCESS_KEY = "AccessKey"
SECRET_KEY = "SecretKey"


def charm_resources(metadata_file="charmcraft.yaml") -> Dict[str, str]:
    with open(metadata_file, "r") as file:
        metadata = yaml.safe_load(file)
    resources = {}
    for res, data in metadata["resources"].items():
        resources[res] = data["upstream-source"]
    return resources


async def configure_minio(ops_test: OpsTest, bucket_name="loki"):
    minio_addr = await get_unit_address(ops_test, "minio", 0)
    mc_client = Minio(
        f"{minio_addr}:9000",
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False,
    )
    # create bucket
    found = mc_client.bucket_exists(bucket_name)
    if not found:
        mc_client.make_bucket(bucket_name)


async def configure_s3_integrator(
    ops_test: OpsTest, s3_app: str = "s3", bucket_name: str = "loki"
):
    assert ops_test.model is not None
    config = {
        "access-key": ACCESS_KEY,
        "secret-key": SECRET_KEY,
    }
    s3_integrator_app: Application = ops_test.model.applications[s3_app]  # type: ignore
    s3_integrator_leader: Unit = s3_integrator_app.units[0]

    await s3_integrator_app.set_config(
        {
            "endpoint": f"minio-0.minio-endpoints.{ops_test.model.name}.svc.cluster.local:9000",
            "bucket": bucket_name,
        }
    )
    action = await s3_integrator_leader.run_action("sync-s3-credentials", **config)
    action_result = await action.wait()
    assert action_result.status == "completed"


async def get_unit_address(ops_test: OpsTest, app_name: str, unit_no: int) -> str:
    assert ops_test.model is not None
    status = await ops_test.model.get_status()
    app = status["applications"][app_name]
    if app is None:
        assert False, f"no app exists with name {app_name}"
    unit = app["units"].get(f"{app_name}/{unit_no}")
    if unit is None:
        assert False, f"no unit exists in app {app_name} with index {unit_no}"
    return unit["address"]


async def get_grafana_datasources_from_client_localhost(
    ops_test: OpsTest,
    grafana_app: str = "grafana",
) -> List[Any]:
    """Get Grafana datasources from the test host machine (outside the cluster)."""
    assert ops_test.model is not None
    grafana_leader: Unit = ops_test.model.applications[grafana_app].units[0]  # type: ignore
    action = await grafana_leader.run_action("get-admin-password")
    action_result = await action.wait()
    admin_password = action_result.results["admin-password"]
    grafana_url = await get_unit_address(ops_test, grafana_app, 0)
    url = f"http://admin:{admin_password}@{grafana_url}:3000/api/datasources"

    # Run query from host
    response = requests.get(url)
    assert response.status_code == 200
    return response.json()


async def get_grafana_datasources_from_client_pod(
    ops_test: OpsTest,
    source_pod: str,
    grafana_app: str = "grafana",
) -> List[Any]:
    """Get Grafana datasources from inside a pod (within the cluster)."""
    assert ops_test.model is not None
    grafana_leader: Unit = ops_test.model.applications[grafana_app].units[0]  # type: ignore
    action = await grafana_leader.run_action("get-admin-password")
    action_result = await action.wait()
    admin_password = action_result.results["admin-password"]
    grafana_url = await get_unit_address(ops_test, grafana_app, 0)
    url = f"http://admin:{admin_password}@{grafana_url}:3000/api/datasources"

    # Run query from within a pod using juju exec (needed for service mesh)
    action = await ops_test.model.applications[source_pod.split("/")[0]].units[
        int(source_pod.split("/")[1])
    ].run(f"curl -s {url}")
    result = await action.wait()

    response_text = result.results.get("stdout", result.results.get("Stdout", ""))
    return json.loads(response_text)


async def get_prometheus_targets_from_client_localhost(
    ops_test: OpsTest,
    prometheus_app: str = "prometheus",
) -> Dict[str, Any]:
    """Get Prometheus scrape targets from the test host machine (outside the cluster)."""
    assert ops_test.model is not None
    prometheus_url = await get_unit_address(ops_test, prometheus_app, 0)
    url = f"http://{prometheus_url}:9090/api/v1/targets"

    # Run query from host
    response = requests.get(url)
    assert response.status_code == 200
    response_json = response.json()

    assert response_json["status"] == "success"
    return response_json["data"]


async def get_prometheus_targets_from_client_pod(
    ops_test: OpsTest,
    source_pod: str,
    prometheus_app: str = "prometheus",
) -> Dict[str, Any]:
    """Get Prometheus scrape targets from inside a pod (within the cluster)."""
    assert ops_test.model is not None
    prometheus_url = await get_unit_address(ops_test, prometheus_app, 0)
    url = f"http://{prometheus_url}:9090/api/v1/targets"

    # Run query from within a pod using juju exec (needed for service mesh)
    action = await ops_test.model.applications[source_pod.split("/")[0]].units[
        int(source_pod.split("/")[1])
    ].run(f"curl -s {url}")
    result = await action.wait()

    response_text = result.results.get("stdout", result.results.get("Stdout", ""))
    response_json = json.loads(response_text)

    assert response_json["status"] == "success"
    return response_json["data"]


async def query_loki_series_from_client_localhost(
    ops_test: OpsTest,
    coordinator_app: str = "loki",
) -> Dict[str, Any]:
    """Query Loki series API from the test host machine (outside the cluster)."""
    assert ops_test.model is not None

    # Run query from host
    loki_url = await get_unit_address(ops_test, coordinator_app, 0)
    response = requests.get(f"http://{loki_url}:8080/loki/api/v1/series")
    assert response.status_code == 200
    response_json = response.json()

    assert response_json["status"] == "success"
    return response_json


async def query_loki_series_from_client_pod(
    ops_test: OpsTest,
    source_pod: str,
    coordinator_app: str = "loki",
) -> Dict[str, Any]:
    """Query Loki series API from inside a pod (within the cluster)."""
    assert ops_test.model is not None

    # Run query from within a pod using juju exec (needed for service mesh)
    loki_url = f"{coordinator_app}.{ops_test.model.name}.svc.cluster.local"
    url = f"http://{loki_url}:8080/loki/api/v1/series"

    action = await ops_test.model.applications[source_pod.split("/")[0]].units[
        int(source_pod.split("/")[1])
    ].run(f"curl -s {url}")
    result = await action.wait()

    response_text = result.results.get("stdout", result.results.get("Stdout", ""))
    response_json = json.loads(response_text)

    assert response_json["status"] == "success"
    return response_json


async def get_traefik_proxied_endpoints(
    ops_test: OpsTest, traefik_app: str = "traefik"
) -> Dict[str, Any]:
    assert ops_test.model is not None
    traefik_leader: Unit = ops_test.model.applications[traefik_app].units[0]  # type: ignore
    action = await traefik_leader.run_action("show-proxied-endpoints")
    action_result = await action.wait()
    return json.loads(action_result.results["proxied-endpoints"])


async def deploy_tempo_cluster(ops_test: OpsTest, cos_channel: str):
    """Deploys tempo in its HA version together with minio and s3-integrator."""
    assert ops_test.model
    tempo_app = "tempo"
    worker_app = "tempo-worker"
    s3_app = "s3-tempo"
    tempo_worker_charm_url, worker_channel = "tempo-worker-k8s", cos_channel
    tempo_coordinator_charm_url, coordinator_channel = "tempo-coordinator-k8s", cos_channel
    await ops_test.model.deploy(
        tempo_worker_charm_url, application_name=worker_app, channel=worker_channel, trust=True
    )
    await ops_test.model.deploy(
        tempo_coordinator_charm_url,
        application_name=tempo_app,
        channel=coordinator_channel,
        trust=True,
    )

    await ops_test.model.deploy("s3-integrator", channel="edge", application_name=s3_app)

    await ops_test.model.integrate(f"{tempo_app}:s3", f"{s3_app}:s3-credentials")
    await ops_test.model.integrate(f"{tempo_app}:tempo-cluster", f"{worker_app}:tempo-cluster")

    await configure_minio(ops_test, bucket_name="tempo")
    await ops_test.model.wait_for_idle(apps=[s3_app], status="blocked")
    await configure_s3_integrator(ops_test, bucket_name="tempo", s3_app=s3_app)

    async with ops_test.fast_forward():
        await ops_test.model.wait_for_idle(
            apps=[tempo_app, worker_app, s3_app],
            status="active",
            timeout=2000,
            idle_period=30,
            # TODO: remove when https://github.com/canonical/tempo-coordinator-k8s-operator/issues/90 is fixed
            raise_on_error=False,
        )


def get_traces(tempo_host: str, service_name="tracegen-otlp_http", tls=True):
    """Get traces directly from Tempo REST API."""
    url = f"{'https' if tls else 'http'}://{tempo_host}:3200/api/search?tags=service.name={service_name}"
    req = requests.get(
        url,
        verify=False,
    )
    assert req.status_code == 200
    traces = json.loads(req.text)["traces"]
    return traces


@retry(stop=stop_after_attempt(15), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_traces_patiently(tempo_host, service_name="tracegen-otlp_http", tls=True):
    """Get traces directly from Tempo REST API, but also try multiple times.

    Useful for cases when Tempo might not return the traces immediately (its API is known for returning data in
    random order).
    """
    traces = get_traces(tempo_host, service_name=service_name, tls=tls)
    assert len(traces) > 0
    return traces


async def get_application_ip(ops_test: OpsTest, app_name: str) -> str:
    """Get the application IP address."""
    assert ops_test.model
    status = await ops_test.model.get_status()
    app = status["applications"][app_name]
    return app.public_address


# TODO: this is a workaround. the ingress provider should provide the proxied-endpoints. See https://github.com/canonical/istio-ingress-k8s-operator/issues/108.
# Update this after the above issue is fixed.
def get_istio_ingress_ip(ops_test: OpsTest, app_name: str = "istio-ingress"):
    """Get the istio-ingress public IP address from Kubernetes."""
    gateway_resource = create_namespaced_resource(
        group="gateway.networking.k8s.io",
        version="v1",
        kind="Gateway",
        plural="gateways",
    )
    client = Client()
    gateway = client.get(gateway_resource, app_name, namespace=ops_test.model.name)  # type: ignore
    if gateway.status and gateway.status.get("addresses"):  # type: ignore
        return gateway.status["addresses"][0]["value"]  # type: ignore
    raise ValueError(f"No ingress address found for {app_name}")


async def service_mesh(
    enable: bool,
    ops_test: OpsTest,
    beacon_app_name: str,
    apps_to_be_related_with_beacon: List[str],
):
    """Enable or disable the service-mesh in the model.

    This puts the entire model, that the beacon app is part of, on mesh.
    This integrates the apps_to_be_related_with_beacon with the beacon app via the `service-mesh` relation.
    """
    assert ops_test.model is not None
    await ops_test.model.applications[beacon_app_name].set_config(
        {"model-on-mesh": str(enable).lower()}
    )
    # Wait for all active state before further actions.
    # The wait is necessary to make sure all the charms have recovered from the network changes.
    await ops_test.model.wait_for_idle(
        status="active",
        timeout=1000,
        raise_on_error=False,
    )
    if enable:
        for app in apps_to_be_related_with_beacon:
            await ops_test.model.integrate(f"{beacon_app_name}:service-mesh", f"{app}:service-mesh")
    else:
        for app in apps_to_be_related_with_beacon:
            await ops_test.model.applications[beacon_app_name].remove_relation(
                f"{beacon_app_name}:service-mesh", f"{app}:service-mesh"
            )
    await ops_test.model.wait_for_idle(
        status="active",
        timeout=1000,
        idle_period=30,
        raise_on_error=False,
    )
