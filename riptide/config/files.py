import os
import re
from appdirs import user_config_dir

RIPTIDE_PROJECT_CONFIG_NAME = 'riptide.yml'
RIPTIDE_PROJECT_META_FOLDER_NAME = '_riptide'
RIPTIDE_PROJECT_SETUP_FLAG_FILENAME = '.setup_flag'

# The path of the source code to be mounted INSIDE the containers
CONTAINER_SRC_PATH = '/src'

# The ~ path inside the running command container
CONTAINER_HOME_PATH = "/home/riptide"


def is_path_root(path):
    real_path = os.path.realpath(path)
    parent_real_path = os.path.realpath(os.path.join(real_path, '..'))
    return real_path == parent_real_path


def __discover_project_file__step(path):
    potential_path = os.path.join(path, RIPTIDE_PROJECT_CONFIG_NAME)
    if os.path.exists(potential_path):
        return potential_path
    if is_path_root(path):
        return None
    return __discover_project_file__step(os.path.join(path, '..'))


def discover_project_file():
    return __discover_project_file__step(os.getcwd())


def riptide_assets_dir():
    # TODO TEMPORARY WINDOWS TESTS
    #return "C:\\Users\\marco\\Desktop\\riptide_assets"
    this_folder = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_folder, '..', '..', 'assets')


def riptide_main_config_file():
    return os.path.join(riptide_config_dir(), 'config.yml')


def riptide_projects_file():
    return os.path.join(riptide_config_dir(), 'projects.json')


def riptide_ports_config_file():
    return os.path.join(riptide_config_dir(), 'ports.json')


def riptide_local_repositories_path():
    return os.path.join(riptide_config_dir(), 'repos')


def riptide_config_dir():
    return user_config_dir('riptide', False)


def get_project_meta_folder(project_folder_path):
    """
    Get the path to the _riptide folder inside of a project.
    project_folder_path is the folder that the config file of the project is in.
    If the folder does not exist if will be created
    """
    path = os.path.join(project_folder_path, RIPTIDE_PROJECT_META_FOLDER_NAME)
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def get_project_setup_flag_path(project_folder_path):
    """Returns the path to the file acting as flag to mark whether the project was set up or not."""
    return os.path.join(
        get_project_meta_folder(project_folder_path),
        RIPTIDE_PROJECT_SETUP_FLAG_FILENAME
    )


def get_current_relative_project_path(project_folder_path):
    """
    Returns the current path relative to the project root
    """
    return os.path.relpath(os.getcwd(), start=project_folder_path)


def get_current_relative_src_path(project):
    """
    Returns the current path relative to the specified src path. If outside of src, returns .
    """
    src = project["src"]
    result = os.path.relpath(os.getcwd(), start=os.path.join(project.folder(), src))
    if result[0:2] == "..":
        return "."
    return result


def remove_all_special_chars(string):
    return re.sub(r"[^a-zA-Z0-9]", "-", string)


def path_in_project(path, project):
    """Check if a path is within a project (a subdirectory of it. Symlinks are ignored)."""
    return path.startswith(os.path.abspath(project.folder()) + os.sep)
