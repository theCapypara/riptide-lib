"""
Functions to load the system configuration and/or projects.
"""
import json
import os
from typing import TYPE_CHECKING

from riptide.config import repositories
from riptide.config.document.config import Config
from riptide.config.document.project import Project
from riptide.config.files import discover_project_file, riptide_main_config_file, riptide_projects_file

if TYPE_CHECKING:
    from riptide.config.document.config import Config
    from riptide.config.document.project import Project


def load_config(project_file=None, update_repositories=False, update_func=lambda msg: None) -> 'Config':
    """
    Loads the specified project file and the system user configuration.
    If no project file is specified, it is auto-detected.

    If the project config could not be found, the project key in the system
    config will not exist. If the system config itself could not be found,
    a FileNotFound error is raised.

    The loaded project is placed in the ``project`` field of the config.
    The path to the project is place in the ``$path`` field of the project.

    :param project_file: Project file to load or None for auto-discovery
    :param update_repositories: Update repositories defined in system config
    :param update_func: If update_repositories is set: Function to execute for status updates of repository updating
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
    system_config.validate()

    # The user is not allowed to add a project entry to their main config file
    if "project" in system_config:
        del system_config["project"]

    # Update repositories
    if update_repositories:
        repositories.update(system_config, update_func)
    repos = repositories.collect(system_config)

    if project_path is not None:
        project_path = os.path.abspath(project_path)
        try:
            project_config = Project.from_yaml(project_path)
            project_config["$path"] = project_path

            project_config.resolve_and_merge_references(repos)

            system_config["project"] = project_config
            project_config.parent_doc = system_config
        except FileNotFoundError:
            pass

    system_config.process_vars()

    system_config.validate()

    return system_config


def load_projects() -> dict:
    """Loads the contents of the projects.json file and returns them."""
    projects = {}
    if os.path.exists(riptide_projects_file()):
        with open(riptide_projects_file(), mode='r') as file:
            projects = json.load(file)
    return projects


def load_config_by_project_name(name: str) -> 'Config':
    """
    Load project by entry in projects.json.

    :func:`load_config` is used for the actual loading.
    """
    projects = load_projects()
    if name not in projects:
        raise Exception("todo")  # todo ProjectNotFoundError
    system_config = load_config(projects[name])  # may raise FileNotFound
    if "project" not in system_config:
        raise FileNotFoundError("todo")  # todo
    return system_config


def write_project(project: 'Project', rename=False):
    """
    Write project to projects.json if not already written.

    Throws an error if a project with the given name,
    but a different path exists, if rename is not specifed.

    :param project:             Project object
    :param rename:              Rename an existing project entry, if found.
    """
    projects = load_projects()

    # xxx: This doesn't look really nice to understand. Basically, check if the project is
    #      already defined in the projects file. If yes and the path is the same we don't
    #      need to do anything. If not and rename is not passed, thrown an error, if
    #      rename is passed or if the path for the project didn't exist yet: Write it to the file.
    changed = True
    if project['name'] in projects:
        changed = False
        if projects[project['name']] != project['$path']:
            changed = True
            if not rename:
                raise FileExistsError(
                    'The Riptide project named %s is already located at %s but your current project file is in %s.\n'
                    'Each project name can only be mapped to one path. If you want to "rename" %s to use this '
                    'new path, pass the --rename flag, otherwise rename the project in the riptide.yml file.\n'
                    'If you want to edit these mappings manually, have a look at the file %s.'
                    % (project['name'], projects[project['name']], project['$path'],
                       project['name'], riptide_projects_file())
                )
    if changed:
        projects[project['name']] = project['$path']
        with open(riptide_projects_file(), mode='w') as file:
            json.dump(projects, file)
    if rename:
        print("Project reference renamed.")
        print("%s -> %s" % (project['name'], projects[project['name']]))
        exit(0)
