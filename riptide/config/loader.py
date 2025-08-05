"""
Functions to load the system configuration and/or projects.
"""

import json
import os
from collections import OrderedDict
from typing import TYPE_CHECKING

from configcrunch import load_multiple_yml
from riptide.config import repositories
from riptide.config.document.config import Config
from riptide.config.document.project import Project
from riptide.config.files import discover_project_file, riptide_main_config_file, riptide_projects_file
from riptide.plugin.loader import load_plugins

if TYPE_CHECKING:
    from riptide.config.document.config import Config
    from riptide.config.document.project import Project


RESERVED_NAMES = [
    "control"  # Riptide Mission Control endpoint on Proxy Server
]
LOCAL_PROJECT_FILENAME = "riptide.local.yml"


def load_config(project_file=None, skip_project_load=False, enable_local_project_config=True) -> "Config":
    """
    Loads the specified project file and the system user configuration.
    If no project file is specified, it is auto-detected. Project loading can be
    disabled by setting skip_project_load to False.

    If in the directory of the project file a ``riptide.local.yml`` exists, this file
    is also loaded and merged into the project (last). This can be disabled by setting
    ``enable_local_project_config`` to False.

    If the project config could not be found, the project key in the system
    config will not exist. If the system config itself could not be found,
    a FileNotFound error is raised.

    The loaded project is placed in the ``project`` field of the config.
    The path to the project is place in the ``$path`` field of the project.

    Also propagates the loaded config to all loaded plugins.

    :param project_file: Project file to load or None for auto-discovery
    :param skip_project_load: Skip project loading. If True, the project_file setting will be ignored
    :param enable_local_project_config: If true, load the `riptide.local.yml` as well.
    :return: :class:`riptide.config.document.config.Config` object.
    :raises: :class:`FileNotFoundError`: If the system config was not found
    :raises: :class:`schema.SchemaError`: On validation errors
    """

    config_path = riptide_main_config_file()

    if project_file:
        project_path = project_file
    else:
        project_path = discover_project_file()

    system_config = Config.from_yaml(config_path)

    # The user is not allowed to add a project entry to their main config file
    if system_config.internal_contains("project"):
        system_config.internal_delete("project")

    system_config.upgrade()
    system_config.validate()

    repos = repositories.collect(system_config)

    if project_path is not None and not skip_project_load:
        project_path = os.path.abspath(project_path)
        local_project_path = os.path.join(os.path.dirname(project_path), LOCAL_PROJECT_FILENAME)
        try:
            if enable_local_project_config and os.path.exists(local_project_path):
                project_config = load_multiple_yml(Project, project_path, local_project_path)
            else:
                project_config = load_multiple_yml(Project, project_path)
            project_config.internal_set("$path", project_path)

            project_config.resolve_and_merge_references(repos)

            system_config.internal_set("project", project_config)
            project_config.parent_doc = system_config
        except FileNotFoundError:
            pass

    system_config.process_vars()

    system_config.validate()
    system_config.freeze()

    for plugin in load_plugins().values():
        plugin.after_reload_config(system_config)

    return system_config


def load_projects(sort=False) -> dict:
    """
    Loads the contents of the projects.json file and returns them.
    If sort is True, they are ordered alphabetically.
    """
    projects = {}
    if os.path.exists(riptide_projects_file()):
        with open(riptide_projects_file()) as file:
            projects = json.load(file)
    if not sort:
        return projects
    return OrderedDict(sorted(projects.items()))


def load_config_by_project_name(name: str) -> "Config":
    """
    Load project by entry in projects.json.

    :func:`load_config` is used for the actual loading.
    """
    projects = load_projects()
    if name not in projects:
        raise FileNotFoundError("Project was not found.")
    system_config = load_config(projects[name])  # may raise FileNotFound
    if "project" not in system_config:
        raise Exception("Unknown error.")
    return system_config


def write_project(project: "Project", rename=False):
    """
    Write project to projects.json if not already written.

    Throws an error if a project with the given name,
    but a different path exists, if rename is not specifed.

    A blacklist (RESERVED_NAMES) is checked, if the project name is on the blacklist,
    Riptide refuses to load it. The blacklist contains reserved names.

    :param project:             Project object
    :param rename:              Rename an existing project entry, if found.
    """

    # Check reserved names
    if project.internal_get("name") in RESERVED_NAMES:
        raise FileExistsError(
            f"The project name {project.internal_get('name')} is reserved by Riptide. "
            f"Please use a different name for your project."
        )

    projects = load_projects()

    # xxx: This doesn't look really nice to understand. Basically, check if the project is
    #      already defined in the projects file. If yes and the path is the same we don't
    #      need to do anything. If not and rename is not passed, thrown an error, if
    #      rename is passed or if the path for the project didn't exist yet: Write it to the file.
    changed = True
    if project.internal_get("name") in projects:
        changed = False
        if projects[project.internal_get("name")] != project.internal_get("$path"):
            changed = True
            if not rename:
                raise FileExistsError(
                    f"The Riptide project named {project.internal_get('name')} is already located at "
                    f"{projects[project.internal_get('name')]} but your current project file is at {project.internal_get('$path')}.\n"
                    f'Each project name can only be mapped to one path. If you want to "rename" {project.internal_get("name")} to use '
                    f"this new path, pass the --rename flag, otherwise rename the project in the riptide.yml file.\n"
                    f"If you want to edit these mappings manually, have a look at the file {riptide_projects_file()}."
                )
    if changed:
        projects[project.internal_get("name")] = project.internal_get("$path")
        with open(riptide_projects_file(), mode="w") as file:
            json.dump(projects, file)
    if rename:
        print("Project reference renamed.")
        print(f"{project.internal_get('name')} -> {projects[project.internal_get('name')]}")
        exit(0)


def remove_project(project_name: str):
    """
    Remove a project from the projects json list
    :param project_name:
    :return:
    """
    projects = load_projects()
    del projects[project_name]
    with open(riptide_projects_file(), mode="w") as file:
        json.dump(projects, file)
