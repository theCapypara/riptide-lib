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
from typing import Tuple, Union


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

    @abc.abstractmethod
    def assert_running(self, engine_obj, project, services):
        """Check that the services are actually running"""
        pass

    @abc.abstractmethod
    def assert_not_running(self, engine_obj, project, services):
        """Check that the services are actually non present"""

    @abc.abstractmethod
    def get_permissions_at(self, path, engine_obj, project, service) -> Tuple[int, int, int]:
        """
        Returns for path the owner, group and octal mode as tuple.
        Path is interpreted relative to container's current working directory
        retuns: (ouid, ogid, mode)
        """

    @abc.abstractmethod
    def get_env(self, env, engine_obj, project, service) -> Union[str, None]:
        """
        Returns the value of the environment variable env. MUST read directly via shell from container.
        If the env variable is not set, must return None
        """
