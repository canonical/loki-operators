# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import logging
from typing import Any, Dict, List

import jubilant
import requests
from jubilant import Juju
from lightkube import Client
from lightkube.generic_resource import create_namespaced_resource
from minio import Minio
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

ACCESS_KEY = "AccessKey"
SECRET_KEY = "SecretKey"


def configure_minio(juju: Juju, bucket_name: str = "loki"):
    """Create the bucket in Minio for object storage."""
    minio_addr = get_unit_address(juju, "minio", 0)
    mc_client = Minio(
        f"{minio_addr}:9000",
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False,
    )
    found = mc_client.bucket_exists(bucket_name)
    if not found:
        mc_client.make_bucket(bucket_name)


def configure_s3_integrator(juju: Juju, s3_app: str = "s3", bucket_name: str = "loki"):
    """Configure the S3 integrator charm with Minio credentials."""
    juju.config(s3_app, {
        "endpoint": f"minio-0.minio-endpoints.{juju.model}.svc.cluster.local:9000",
        "bucket": bucket_name,
    })
    task = juju.run(f"{s3_app}/leader", "sync-s3-credentials", params={
        "access-key": ACCESS_KEY,
        "secret-key": SECRET_KEY,
    })
    assert task.status == "completed"


def get_unit_address(juju: Juju, app_name: str, unit_no: int) -> str:
    """Get the address of a specific unit."""
    status = juju.status()
    return status.apps[app_name].units[f"{app_name}/{unit_no}"].address


def get_grafana_datasources_from_client_localhost(
    juju: Juju,
    grafana_app: str = "grafana",
) -> List[Any]:
    """Get Grafana datasources from the test host machine (outside the cluster)."""
    result = juju.run(f"{grafana_app}/leader", "get-admin-password")
    admin_password = result.results["admin-password"]
    grafana_url = get_unit_address(juju, grafana_app, 0)
    url = f"http://admin:{admin_password}@{grafana_url}:3000/api/datasources"

    response = requests.get(url)
    assert response.status_code == 200
    return response.json()


def get_loki_rules_from_grafana(
    juju: Juju,
    grafana_app: str = "grafana",
) -> Dict[str, Any]:
    """Query Loki alert rules through Grafana's Prometheus-compatible API.

    This exercises the nginx routing in the Loki coordinator for the
    /prometheus/api/v1/rules endpoint, which Grafana uses to fetch alert rules.
    """
    result = juju.run(f"{grafana_app}/leader", "get-admin-password")
    admin_password = result.results["admin-password"]
    grafana_url = get_unit_address(juju, grafana_app, 0)
    base_url = f"http://admin:{admin_password}@{grafana_url}:3000"

    # Find the Loki datasource UID
    response = requests.get(f"{base_url}/api/datasources")
    assert response.status_code == 200
    datasources = response.json()

    loki_uid = None
    for ds in datasources:
        if "loki" in ds.get("name", "").lower() or ds.get("type") == "loki":
            loki_uid = ds.get("uid")
            break
    assert loki_uid is not None, "Loki datasource not found in Grafana"

    # Query alert rules through Grafana's Prometheus-compatible proxy endpoint
    response = requests.get(f"{base_url}/api/prometheus/{loki_uid}/api/v1/rules")
    assert response.status_code == 200
    response_json = response.json()
    
    # Grafana treats a no data as a 200 as well, so to ensure that there are Loki rules, we checks that the groups are not empty.
    assert response_json.get("data", {}).get("groups", [])
    return response_json


def get_grafana_datasources_from_client_pod(
    juju: Juju,
    source_pod: str,
    grafana_app: str = "grafana",
) -> List[Any]:
    """Get Grafana datasources from inside a pod (within the cluster)."""
    result = juju.run(f"{grafana_app}/leader", "get-admin-password")
    admin_password = result.results["admin-password"]
    grafana_url = get_unit_address(juju, grafana_app, 0)
    url = f"http://admin:{admin_password}@{grafana_url}:3000/api/datasources"

    task = juju.exec(f"curl -s {url}", unit=source_pod)
    return json.loads(task.stdout)


def get_prometheus_targets_from_client_localhost(
    juju: Juju,
    prometheus_app: str = "prometheus",
) -> Dict[str, Any]:
    """Get Prometheus scrape targets from the test host machine (outside the cluster)."""
    prometheus_url = get_unit_address(juju, prometheus_app, 0)
    url = f"http://{prometheus_url}:9090/api/v1/targets"

    response = requests.get(url)
    assert response.status_code == 200
    response_json = response.json()

    assert response_json["status"] == "success"
    return response_json["data"]


def get_prometheus_targets_from_client_pod(
    juju: Juju,
    source_pod: str,
    prometheus_app: str = "prometheus",
) -> Dict[str, Any]:
    """Get Prometheus scrape targets from inside a pod (within the cluster)."""
    prometheus_url = get_unit_address(juju, prometheus_app, 0)
    url = f"http://{prometheus_url}:9090/api/v1/targets"

    task = juju.exec(f"curl -s {url}", unit=source_pod)
    response_json = json.loads(task.stdout)

    assert response_json["status"] == "success"
    return response_json["data"]


def query_loki_series_from_client_localhost(
    juju: Juju,
    coordinator_app: str = "loki",
) -> Dict[str, Any]:
    """Query Loki series API from the test host machine (outside the cluster)."""
    loki_url = get_unit_address(juju, coordinator_app, 0)
    response = requests.get(f"http://{loki_url}:8080/loki/api/v1/series")
    assert response.status_code == 200
    response_json = response.json()

    assert response_json["status"] == "success"
    return response_json


def query_loki_series_from_client_pod(
    juju: Juju,
    source_pod: str,
    coordinator_app: str = "loki",
) -> Dict[str, Any]:
    """Query Loki series API from inside a pod (within the cluster)."""
    loki_url = f"{coordinator_app}.{juju.model}.svc.cluster.local"
    url = f"http://{loki_url}:8080/loki/api/v1/series"

    task = juju.exec(f"curl -s {url}", unit=source_pod)
    response_json = json.loads(task.stdout)

    assert response_json["status"] == "success"
    return response_json


def get_traefik_proxied_endpoints(
    juju: Juju, traefik_app: str = "traefik"
) -> Dict[str, Any]:
    """Get proxied endpoints from Traefik."""
    result = juju.run(f"{traefik_app}/leader", "show-proxied-endpoints")
    return json.loads(result.results["proxied-endpoints"])


def deploy_tempo_cluster(juju: Juju, cos_channel: str):
    """Deploy Tempo in its HA version together with Minio and s3-integrator."""
    tempo_app = "tempo"
    worker_app = "tempo-worker"
    s3_app = "s3-tempo"

    juju.deploy("tempo-worker-k8s", app=worker_app, channel=cos_channel, trust=True)
    juju.deploy("tempo-coordinator-k8s", app=tempo_app, channel=cos_channel, trust=True)
    juju.deploy("s3-integrator", app=s3_app, channel="edge")

    juju.integrate(f"{tempo_app}:s3", f"{s3_app}:s3-credentials")
    juju.integrate(f"{tempo_app}:tempo-cluster", f"{worker_app}:tempo-cluster")

    configure_minio(juju, bucket_name="tempo")
    juju.wait(lambda status: jubilant.all_blocked(status, s3_app), timeout=1000)
    configure_s3_integrator(juju, bucket_name="tempo", s3_app=s3_app)

    juju.wait(
        lambda status: jubilant.all_active(status, tempo_app, worker_app, s3_app),
        timeout=2000,
        delay=5,
        successes=3,
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
def get_traces_patiently(tempo_host, service_name="tracegen-otlp_http", tls=True):
    """Get traces directly from Tempo REST API, but also try multiple times.

    Useful for cases when Tempo might not return the traces immediately (its API is known
    for returning data in random order).
    """
    traces = get_traces(tempo_host, service_name=service_name, tls=tls)
    assert len(traces) > 0
    return traces


def get_application_ip(juju: Juju, app_name: str) -> str:
    """Get the application IP address."""
    status = juju.status()
    return status.apps[app_name].address


# TODO: this is a workaround. The ingress provider should provide the proxied-endpoints.
# See https://github.com/canonical/istio-ingress-k8s-operator/issues/108.
def get_istio_ingress_ip(juju: Juju, app_name: str = "istio-ingress") -> str:
    """Get the istio-ingress public IP address from Kubernetes."""
    gateway_resource = create_namespaced_resource(
        group="gateway.networking.k8s.io",
        version="v1",
        kind="Gateway",
        plural="gateways",
    )
    client = Client()
    gateway = client.get(gateway_resource, app_name, namespace=juju.model)
    if gateway.status and gateway.status.get("addresses"):  # type: ignore
        return gateway.status["addresses"][0]["value"]  # type: ignore
    raise ValueError(f"No ingress address found for {app_name}")


def service_mesh(
    enable: bool,
    juju: Juju,
    beacon_app_name: str,
    apps_to_be_related_with_beacon: List[str],
):
    """Enable or disable the service-mesh in the model.

    This puts the entire model, that the beacon app is part of, on mesh.
    This integrates the apps_to_be_related_with_beacon with the beacon app
    via the ``service-mesh`` relation.
    """
    juju.config(beacon_app_name, {"model-on-mesh": str(enable).lower()})
    juju.wait(jubilant.all_active, timeout=1000)
    if enable:
        for app in apps_to_be_related_with_beacon:
            juju.integrate(f"{beacon_app_name}:service-mesh", f"{app}:service-mesh")
    else:
        for app in apps_to_be_related_with_beacon:
            juju.remove_relation(f"{beacon_app_name}:service-mesh", f"{app}:service-mesh")
    juju.wait(jubilant.all_active, timeout=1000)
