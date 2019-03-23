import os
import shutil
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Union, List

from distutils.dir_util import copy_tree

from riptide.config.files import path_in_project
from riptide.engine.results import StartStopResultStep, MultiResultQueue


RIPTIDE_HOST_HOSTNAME = "host.riptide.internal"  # the engine has to make the host reachable under this hostname


class ExecError(BaseException):
    pass


class AbstractEngine(ABC):
    @abstractmethod
    def start_project(self, project: 'Project', services: List[str]) -> MultiResultQueue[StartStopResultStep]:
        """
        Starts all services in the project
        :type project: 'Project'
        :param services: Names of the services to start
        :return: MultiResultQueue[StartResult]
        """
        pass

    @abstractmethod
    def stop_project(self, project: 'Project', services: List[str]) -> MultiResultQueue[StartStopResultStep]:
        """
        Stops all services in the project
        :type project: 'Project'
        :param services: Names of the services to stop
        :return: MultiResultQueue[StopResult]
        """
        pass

    @abstractmethod
    def status(self, project: 'Project', system_config: 'Config') -> Dict[str, bool]:
        """
        Returns the status for the given project (whether services are started or not)
        :param system_config: Main system config
        :param project: 'Project'
        :return: StatusResult
        """
        pass

    @abstractmethod
    def address_for(self, project: 'Project', service_name: str) -> Union[None, Tuple[str, int]]:
        """
        Returns the ip address and port of the host providing the service for project.
        :param project: 'Project'
        :param service_name: str
        :return: Tuple[str, int]
        """
        pass

    @abstractmethod
    def cmd(self, project: 'Project', command_name: str, arguments: List[str]) -> None:
        """
        Execute the command identified by command_name in the project environment and
        attach command to stdout/stdin/stderr.
        Returns when the command is finished.
        :param project: 'Project'
        :param command_name: str
        :param arguments: List of arguments
        :return:
        """

    @abstractmethod
    def service_fg(self, project: 'Project', service_name: str, arguments: List[str]) -> None:
        """
        Execute a service and attach output to stdout/stdin/stderr.
        Returns when the service container is finished.

        Following service options are ignored:

        * logging.stdout (is false)
        * logging.stderr (is false)
        * pre_start (is empty)
        * post_start (is empty)
        * roles.src (is set)
        * working_directory (is set to current working directory)

        :param project: 'Project'
        :param service_name: str
        :param arguments: List of arguments
        :return:
        """

    @abstractmethod
    def cmd_detached(self, project: 'Project', command: 'Command', run_as_root=False) -> (int, str):
        """
        Execute the command in the project environment and
        return the exit code (int), stdout/stderr of the command (str).
        Src/Current working directory is not mounted.
        Returns when finished.
        :param run_as_root: Force execution of the command container with the highest possible permissions
        :param project: 'Project'
        :param command: Command Command to run. May not be part of the passed project object but must be treated as such.
        :return:
        """

    @abstractmethod
    def exec(self, project: 'Project', service_name: str, cols=None, lines=None, root=False) -> None:
        """
        Open an interactive shell into service_name and attach stdout/stdin/stderr.
        Returns when the shell is exited.
        :param root: If true, run as root user instead of current shell user
        :param lines: Number of lines in the terminal, optional
        :param cols: Number of columns in the terminal, optional
        :param project: 'Project'
        :param service_name: str
        :return:
        """
        pass

    @abstractmethod
    def pull_images(self, project: 'Project', line_reset='\n', update_func=lambda msg: None) -> None:
        """
        Open an interactive shell into service_name and attach stdout/stdin/stderr.
        Returns when the shell is exited.
        Not fining an image should NOT raise an error and instead print a warning as status report.
        :param project: The project to pull all images for. Applies to all commands and services in project.
        :param line_reset: Characters that represent a line reset for the current terminal.
        :param update_func: Function to send status updates to.
                            Resetting the line via the provided parameter is allowed.
                            Calling it does NOT add new lines (\n).
                            End result should be looking like this::

                                [service/service1] Pulling 'image/name':
                                    Status report... Can use carriage return here.
                                [service/service2] Pulling 'image/name':
                                    Status report... Can use carriage return here.
                                [command/command1] Pulling 'image/name':
                                    Warning: Image not found in repository.

                                Done.

        :return:
        """
        pass

    def path_rm(self, path, project: 'Project'):
        """
        Delete a path. Default is using python builtin functions.
        PATH MUST BE WITHIN PROJECT.

        path was created using an engine service or command.
        If paths created with this engine may not be writable with the user calling riptide,
        override this method to remove the folder using elevated rights (eg. running a Docker container as root).

        Returns without an exception if the path was moved (or didn't exist).
        """
        if not path_in_project(path, project):
            raise PermissionError("Tried to delete a file/directory that is not within the project: %s" % path)
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)

    def path_copy(self, fromm, to, project: 'Project'):
        """
        Copy a path. Default is using python builtin functions. 'to' may not exist already.
        TO PATH MUST BE WITHIN PROJECT.

        See notes at path_rm
        Returns without an exception if the path was copied.
        """
        if not path_in_project(to, project):
            raise PermissionError("Tried to copy into a path that is not within the project: %s -> %s" % fromm, to)
        if os.path.isfile(fromm):
            shutil.copy2(fromm, to)
        else:
            copy_tree(fromm, to)

    @abstractmethod
    def supports_exec(self):
        """
        Whether or not this engine supports exec.
        :return:
        """
        pass
