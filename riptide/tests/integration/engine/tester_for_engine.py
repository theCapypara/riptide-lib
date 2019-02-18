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
    @abc.abstractmethod
    def reset(self, engine_obj):
        """
        For Docker:
            Stop and delete all created containers and created networks. May also clean images
            Issue a warning by printing to the console, if containers needed to be cleaned up,
            stating what needed to be done.
        For others:
            Equivalent to Docker cleanup
        """

    def assert_running(self, project, services):
        """TODO. Add description and make abstractmethod."""
        pass

    def assert_not_running(self, project, services):
        """TODO. Add description and make abstractmethod."""
        pass