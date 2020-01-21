|Riptide|
=========

.. |Riptide| image:: https://riptide-docs.readthedocs.io/en/latest/_images/logo.png
    :alt: Riptide

.. class:: center

    ======================  ===================  ===================  ===================
    *Main packages:*        **lib**              proxy_               cli_
    *Container-Backends:*   engine_docker_
    *Database Drivers:*     db_mysql_
    *Plugins:*              php_xdebug_
    *Related Projects:*     configcrunch_
    *More:*                 docs_                repo_                docker_images_
    ======================  ===================  ===================  ===================

.. _lib:            https://github.com/Parakoopa/riptide-lib
.. _cli:            https://github.com/Parakoopa/riptide-cli
.. _proxy:          https://github.com/Parakoopa/riptide-proxy
.. _configcrunch:   https://github.com/Parakoopa/configcrunch
.. _engine_docker:  https://github.com/Parakoopa/riptide-engine-docker
.. _db_mysql:       https://github.com/Parakoopa/riptide-db-mysql
.. _docs:           https://github.com/Parakoopa/riptide-docs
.. _repo:           https://github.com/Parakoopa/riptide-repo
.. _docker_images:  https://github.com/Parakoopa/riptide-docker-images
.. _php_xdebug:     https://github.com/Parakoopa/riptide-plugin-php-xdebug

|build| |docs| |pypi-version| |pypi-downloads| |pypi-license| |pypi-pyversions| |slack|

.. |build| image:: https://jenkins.riptide.parakoopa.de/buildStatus/icon?job=riptide-lib%2Fmaster
    :target: https://jenkins.riptide.parakoopa.de/blue/organizations/jenkins/riptide-lib/activity
    :alt: Build Status

.. |docs| image:: https://readthedocs.org/projects/riptide-docs/badge/?version=latest
    :target: https://riptide-docs.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |slack| image:: https://slack.riptide.parakoopa.de/badge.svg
    :target: https://slack.riptide.parakoopa.de
    :alt: Join our Slack workspace

.. |pypi-version| image:: https://img.shields.io/pypi/v/riptide-lib
    :target: https://pypi.org/project/riptide-lib/
    :alt: Version

.. |pypi-downloads| image:: https://img.shields.io/pypi/dm/riptide-lib
    :target: https://pypi.org/project/riptide-lib/
    :alt: Downloads

.. |pypi-license| image:: https://img.shields.io/pypi/l/riptide-lib
    :alt: License (MIT)

.. |pypi-pyversions| image:: https://img.shields.io/pypi/pyversions/riptide-lib
    :alt: Supported Python versions

Riptide is a set of tools to manage development environments for web applications.
It's using container virtualization tools, such as `Docker <https://www.docker.com/>`_
to run all services needed for a project.

It's goal is to be easy to use by developers.
Riptide abstracts the virtualization in such a way that the environment behaves exactly
as if you were running it natively, without the need to install any other requirements
the project may have.

Library Package
---------------

This repository contains the library with common code for the Riptide CLI and the Riptide Proxy. Most notably it
contains the interfaces for engine implementations and database drivers and classes for all of the configuration entities
(Apps, Projects, Services, Commands...).

It can be installed via pip by installing ``riptide-lib``.

Tests
-----

Inside the ``riptide.tests package`` are unit tests for the library and integration tests. The integration
tests require you to install at least one engine implementation (eg. ``riptide-engine-docker``). The integration
tests test the Riptide Library itself and the specific engine implementations.

To run the tests, see ``run_tests.sh``.

Documentation
-------------

The complete documentation for Riptide can be found at `Read the Docs <https://riptide-docs.readthedocs.io/en/latest/>`_.