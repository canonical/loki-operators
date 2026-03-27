# Contributing

This guide applies to both charms contained in this repository: ./coordinator and ./worker.

## Overview

This documents explains the processes and practices recommended for contributing enhancements to
this operator.

- Generally, before developing enhancements to this charm, you should consider [opening an issue
  ](https://github.com/canonical/loki-operators/issues) explaining your use case.
- If you would like to chat with us about your use-cases or proposed implementation, you can reach
  us at the [Canonical Observability Matrix public channel](https://matrix.to/#/#cos:ubuntu.com)
  or on [Discourse](https://discourse.charmhub.io/).
- Familiarising yourself with the [Charmed Operator Framework](https://juju.is/docs/sdk) library
  will help you a lot when working on new features or bug fixes.
- All enhancements require review before being merged. Code review typically examines
  - code quality
  - test coverage
  - user experience for Juju administrators this charm.
- Please help us out in ensuring easy to review branches by rebasing your pull request branch onto
  the `main` branch. This also avoids merge commits and creates a linear Git commit history.

## Developing

You can use the environments created by `tox` for development:

```shell
tox --notest -e unit
source .tox/unit/bin/activate
```

### Testing

```shell
tox -e fmt           # update your code according to formatting rules
tox -e lint          # lint the codebase
tox -e unit          # run the unit testing suite
tox -e integration   # run the integration testing suite
tox                  # runs 'lint' and 'unit' environments
```

## Build charm

Build the charms in this git repository using:

```shell
cd ./worker; charmcraft pack
cd ./coordinator; charmcraft pack
```
