"""
This module is the central place for getting the paths to most files and directories
Riptide uses.

Also provides some utility file-related functions.
"""
import os
import pkg_resources
import re
from appdirs import user_config_dir

# Expected name of the project files during auto-discovery
from typing import Optional

RIPTIDE_PROJECT_CONFIG_NAME = 'riptide.yml'
# Name of the meta-directory
RIPTIDE_PROJECT_META_FOLDER_NAME = '_riptide'
# Flag for the CLI to look at to see if setup was completed
RIPTIDE_PROJECT_SETUP_FLAG_FILENAME = '.setup_flag'

# The path of the source code to be mounted INSIDE the containers
CONTAINER_SRC_PATH = '/src'

# The ~ path inside the running command container
CONTAINER_HOME_PATH = "/home/riptide"


def is_path_root(path: str) -> bool:
    """Returns whether or not the given (host) path is the root of the filesystem."""
    real_path = os.path.realpath(path)
    parent_real_path = os.path.realpath(os.path.join(real_path, '..'))
    return real_path == parent_real_path


def _discover_project_file__step(path):
    potential_path = os.path.join(path, RIPTIDE_PROJECT_CONFIG_NAME)
    if os.path.exists(potential_path):
        return potential_path
    if is_path_root(path):
        return None
    return _discover_project_file__step(os.path.join(path, '..'))


def discover_project_file() -> Optional[str]:
    """
    Starting in the current working directory upwards, try to find a project file.

    :return: Path to the first found file or None
    """
    return _discover_project_file__step(os.getcwd())


def riptide_assets_dir() -> str:
    """ Path to the assets directory of riptide_lib. """
    return pkg_resources.resource_filename('riptide', 'assets')


def riptide_main_config_file() -> str:
    """ Path to the main configuration file. """
    return os.path.join(riptide_config_dir(), 'config.yml')


def riptide_projects_file() -> str:
    """ Path to the projects.json file. """
    return os.path.join(riptide_config_dir(), 'projects.json')


def riptide_ports_config_file() -> str:
    """ Path to the ports.json file. """
    return os.path.join(riptide_config_dir(), 'ports.json')


def riptide_local_repositories_path() -> str:
    """ Path to the directory where repositories are stored. """
    return os.path.join(riptide_config_dir(), 'repos')


def riptide_config_dir() -> str:
    """ Path to the system configuration directory. """
    return user_config_dir('riptide', False)


def get_project_meta_folder(project_folder_path: str) -> str:
    """
    Get the path to the _riptide folder inside of a project.

    If the folder does not exist if will be created.

    :param project_folder_path: Folder that the config file of the project is in.
    """
    path = os.path.join(project_folder_path, RIPTIDE_PROJECT_META_FOLDER_NAME)
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def get_project_setup_flag_path(project_folder_path: str) -> str:
    """
    Returns the path to the file acting as flag to mark whether the project was set up or not.

    :param project_folder_path: Folder that the config file of the project is in.
    """
    return os.path.join(
        get_project_meta_folder(project_folder_path),
        RIPTIDE_PROJECT_SETUP_FLAG_FILENAME
    )


def get_current_relative_project_path(project_folder_path: str) -> str:
    """
    Returns the current path relative to the project root

    :param project_folder_path: Folder that the config file of the project is in.
    """
    return os.path.relpath(os.getcwd(), start=project_folder_path)


def get_current_relative_src_path(project: 'Project') -> str:
    """
    For project:
    Returns the current (host) working directory path relative to the specified src path. If outside of src, returns .

    :param project: Project
    """
    src = project["src"]
    result = os.path.relpath(os.getcwd(), start=os.path.join(project.folder(), src))
    if result[0:2] == "..":
        return "."
    return result


def remove_all_special_chars(string: str) -> str:
    """ Removes all characters except letters and numbers and replaces them with ``-``."""
    return re.sub(r"[^a-zA-Z0-9]", "-", string)


def path_in_project(path: str, project: 'Project') -> bool:
    """Check if a path is within a project's directory or a subdirectory of it (symlinks are ignored)."""
    return path.startswith(os.path.abspath(project.folder()) + os.sep)
