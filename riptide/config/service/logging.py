"""Functions for helping processing ``logging`` entries in :class:`riptide.config.document.service.Service` objects"""
import os
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from riptide.config.files import get_project_meta_folder, remove_all_special_chars

if TYPE_CHECKING:
    from riptide.config.document.service import Service

# Folder inside _riptide that contains the logs
FOLDER_FOR_LOGGING = 'logs'

# In-Container path to the log files for logging commands
PATH_OF_COMMAND_OUTPUT_LOGFILES_IN_CONTAINER = '/cmd_logs'

# Paths to the stdout/stderr inside the container
LOGGING_CONTAINER_STDOUT = '/riptide_stdout'
LOGGING_CONTAINER_STDERR = '/riptide_stderr'


def _get_log_path(service):
    project = service.get_project()
    return os.path.join(
        get_project_meta_folder(project.folder()),
        FOLDER_FOR_LOGGING,
        service["$name"]
    )


def create_logging_path(service: 'Service'):
    """Create the logs folder in the project's meta folder (_riptide) and a subfolder for the service."""
    path = _get_log_path(service)
    os.makedirs(path, exist_ok=True)


def get_logging_path_for(service: 'Service', log_name: str) -> str:
    """
    Get the host path to store the log file with the given name at.
    """
    path = _get_log_path(service)
    filename = os.path.join(path, remove_all_special_chars(log_name) + '.log')
    with open(filename, 'a'):
        pass # only open it to create it if it doesn't exist
    os.chmod(filename, 0o666)
    return filename


def get_command_logging_container_path(command_log_name: str) -> str:
    """Returns the path to the log file of a command log command INSIDE a container"""
    return str(PurePosixPath(PATH_OF_COMMAND_OUTPUT_LOGFILES_IN_CONTAINER, command_log_name))
