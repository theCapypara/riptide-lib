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
            Raise a warning, if containers needed to be cleaned up,
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
    def get_permissions_at(self, path, engine_obj, project, service, write_check=True, is_directory=True, as_user=0) -> Tuple[int, int, int, bool]:
        """
        Returns for path the owner, group and octal mode as tuple.
        if write_check and is_directory=True:
            Also returns as a fourth item a real write check by trying to create the file
            '__write_check' as user with id 'as_user' inside the path
        if write_check and is_directory=False:
            Also returns as a fourth item a real write check by trying to append a line to the file as user 'as_user'
        Path is interpreted relative to container's current working directory
        retuns: (ouid, ogid, mode, (write_check or false if parameter write_check=False))
        """

    @abc.abstractmethod
    def get_env(self, env, engine_obj, project, service) -> Union[str, None]:
        """
        Returns the value of the environment variable env. MUST read directly via shell from container.
        If the env variable is not set, must return None
        """

    @abc.abstractmethod
    def get_file(self, file, engine, project, service) -> Union[str, None]:
        """
        Return the content of the file inside the container or None if file does not exist
        """

    @abc.abstractmethod
    def assert_file_exists(self, file, engine, project, service, type='both'):
        """
        Assert that a file or directory at the given path exists
        :type type: str file, dirctory or both
        """

    @abc.abstractmethod
    def create_file(self, path, engine, project, service, as_user=0):
        """
        Try to create a file at the given path
        """
