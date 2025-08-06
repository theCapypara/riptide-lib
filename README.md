# ![Riptide](https://riptide-docs.readthedocs.io/en/latest/_images/logo.png)

[<img src="https://img.shields.io/github/actions/workflow/status/theCapypara/riptide-lib/build.yml" alt="Build Status">](https://github.com/theCapypara/riptide-lib/actions)
[<img src="https://readthedocs.org/projects/riptide-docs/badge/?version=latest" alt="Documentation Status">](https://riptide-docs.readthedocs.io/en/latest/)
[<img src="https://img.shields.io/pypi/v/riptide-lib" alt="Version">](https://pypi.org/project/riptide-lib/)
[<img src="https://img.shields.io/pypi/dm/riptide-lib" alt="Downloads">](https://pypi.org/project/riptide-lib/)
<img src="https://img.shields.io/pypi/l/riptide-lib" alt="License (MIT)">
<img src="https://img.shields.io/pypi/pyversions/riptide-lib" alt="Supported Python versions">

Riptide is a set of tools to manage development environments for web applications.
It's using container virtualization tools, such as [Docker](https://www.docker.com/)
to run all services needed for a project.

Its goal is to be easy to use by developers.
Riptide abstracts the virtualization in such a way that the environment behaves exactly
as if you were running it natively, without the need to install any other requirements
the project may have.

Riptide consists of a few repositories, find the
entire [overview](https://riptide-docs.readthedocs.io/en/latest/development.html) in the documentation.

## Library Package

This repository contains the library with common code for the Riptide CLI and the Riptide Proxy. Most notably it
contains the interfaces for engine implementations and database drivers and classes for all of the configuration
entities
(Apps, Projects, Services, Commands...).

It can be installed via pip by installing `riptide-lib`.

## Tests

Inside the `riptide.tests package` are unit tests for the library and integration tests. The integration
tests require you to install at least one engine implementation (eg. `riptide-engine-docker`). The integration
tests test the Riptide Library itself and the specific engine implementations.

To run the tests, see `run_tests.sh`.

## Documentation

The complete documentation for Riptide can be found at [Read the Docs](https://riptide-docs.readthedocs.io/en/latest/).
