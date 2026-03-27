# loki-operators

This repository hosts two charms following the [coordinated-workers](https://github.com/canonical/cos-coordinated-workers/) pattern.
Together, they deploy and operate Loki, a log aggregation system by Grafana Labs.

The charm in `./coordinator` deploys and operates a configurator charm and an nginx instance responsible for routing traffic to the worker nodes.

The charm in `./worker` deploys and operates one or multiple roles of Loki's distributed architecture.

The coordinator was previously hosted at [canonical/loki-coordinator-k8s-operator](https://github.com/canonical/loki-coordinator-k8s-operator) and the worker at [canonical/loki-worker-k8s-operator](https://github.com/canonical/loki-worker-k8s-operator).
