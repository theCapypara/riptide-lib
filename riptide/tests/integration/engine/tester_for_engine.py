"""
Tester base class for testing engine specific implementation details, singleton.
To be extended by the engines to run different or additional tests. Called by main tests when needed.
Engines that want to be tested have to export their engine implementation and an implementation of
this class in their setup.py.

Example:
        [riptide.engine]
        docker=riptide_engine_docker.engine:DockerEngine
        [riptide.engine.tests]
        docker=riptide_engine_docker.tests.integration.tester:DockerEngineTester
"""
import abc


class AbstractEngineTester(abc.ABC):
    pass
