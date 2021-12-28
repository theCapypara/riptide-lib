|Riptide|
=========

.. |Riptide| image:: https://riptide-docs.readthedocs.io/en/latest/_images/logo.png
    :alt: Riptide

.. class:: center

    ======================  ===================  ===================  ===================
    *Main packages:*        **lib**              proxy_               cli_
    *Container-Backends:*   engine_docker_
    *Database Drivers:*     db_mysql_            db_mongo_
    *Plugins:*              php_xdebug_
    *Kubernetes:*           k8s_client_          k8s_controller_
    *Related Projects:*     configcrunch_
    *More:*                 docs_                repo_                docker_images_
    ======================  ===================  ===================  ===================

.. _lib:            https://github.com/theCapypara/riptide-lib
.. _cli:            https://github.com/theCapypara/riptide-cli
.. _proxy:          https://github.com/theCapypara/riptide-proxy
.. _configcrunch:   https://github.com/theCapypara/configcrunch
.. _engine_docker:  https://github.com/theCapypara/riptide-engine-docker
.. _db_mysql:       https://github.com/theCapypara/riptide-db-mysql
.. _db_mongo:       https://github.com/theCapypara/riptide-db-mongo
.. _docs:           https://github.com/theCapypara/riptide-docs
.. _repo:           https://github.com/theCapypara/riptide-repo
.. _docker_images:  https://github.com/theCapypara/riptide-docker-images
.. _php_xdebug:     https://github.com/theCapypara/riptide-plugin-php-xdebug
.. _k8s_client:     https://github.com/theCapypara/riptide-k8s-client
.. _k8s_controller: https://github.com/theCapypara/riptide-k8s-controller

|build| |docs| |pypi-version| |pypi-downloads| |pypi-license| |pypi-pyversions| |slack|

.. |build| image:: https://img.shields.io/github/workflow/status/theCapypara/riptide-lib/Build,%20test%20and%20publish
    :target: https://github.com/theCapypara/riptide-lib/actions
    :alt: Build Status

.. |docs| image:: https://readthedocs.org/projects/riptide-docs/badge/?version=latest
    :target: https://riptide-docs.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |slack| image:: https://slack.riptide.theCapypara.de/badge.svg
    :target: https://slack.riptide.theCapypara.de
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