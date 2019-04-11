|Riptide|
=========

.. |Riptide| image:: https://riptide-docs.readthedocs.io/en/latest/_images/logo.png
    :alt: Riptide

.. class:: center

    ===================  ===================  ===================  ===================
    *Main packages:*     **lib**              proxy_               cli_
    *Engine-Backends:*   engine_docker_
    *Database Drivers:*  db_mysql_
    *Related Projects:*  configcrunch_
    *More:*              docs_                repo_
    ===================  ===================  ===================  ===================

.. _lib:            https://github.com/Parakoopa/riptide-lib
.. _cli:            https://github.com/Parakoopa/riptide-cli
.. _proxy:          https://github.com/Parakoopa/riptide-proxy
.. _configcrunch:   https://github.com/Parakoopa/configcrunch
.. _engine_docker:  https://github.com/Parakoopa/riptide-engine-docker
.. _db_mysql:       https://github.com/Parakoopa/riptide-db-mysql
.. _docs:           https://github.com/Parakoopa/riptide-docs
.. _repo:           https://github.com/Parakoopa/riptide-repo

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

Tests
-----

Inside the riptide.tests package are unit tests for the library and integration tests. The integration
tests require you to install at least one engine implementation (eg. ``riptide_engine_docker``). The integration
tests test the Riptide Library itself and the specific engine implementations.

To run the tests, see ``run_tests.sh``.

Documentation
-------------

The complete documentation for Riptide can be found at `Read the Docs <https://riptide-docs.readthedocs.io/en/latest/>`_.