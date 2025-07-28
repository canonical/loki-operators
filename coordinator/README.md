# Loki Operator

[![CharmHub Badge](https://charmhub.io/loki-coordinator-k8s/badge.svg)](https://charmhub.io/loki-coordinator-k8s)
[![Release](https://github.com/canonical/loki-coordinator-k8s-operator/actions/workflows/release.yaml/badge.svg)](https://github.com/canonical/loki-k8s-operator/actions/workflows/release.yaml)
[![Discourse Status](https://img.shields.io/discourse/status?server=https%3A%2F%2Fdiscourse.charmhub.io&style=flat&label=CharmHub%20Discourse)](https://discourse.charmhub.io)

This repository contains the source code for a Charmed Operator that drives [Loki](https://grafana.com/oss/loki/) on Kubernetes. It is destined to work together with [loki-worker-k8s](https://charmhub.io/loki-worker-k8s) to deploy and operate Loki, a logging backend backed by Grafana. See [Loki HA documentation](https://discourse.charmhub.io/t/loki-coordinator-k8s-operator-docs-index/15491) for more details.

## Usage

Assuming you have access to a bootstrapped Juju controller on Kubernetes, you can:

```bash
$ juju deploy loki-coordinator-k8s # --trust (use when cluster has RBAC enabled)
```

## OCI Images

This charm, by default, deploys `ghcr.io/canonical/nginx@sha256:6415a2c5f25f1d313c87315a681bdc84be80f3c79c304c6744737f9b34207993` and `nginx/nginx-prometheus-exporter:1.1.0`.

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines
on enhancements to this charm following best practice guidelines, and the
[contributing] doc for developer guidance.

[Loki]: https://grafana.com/oss/loki/
[contributing]: https://github.com/canonical/loki-coordinator-k8s-operator/blob/main/CONTRIBUTING.md
