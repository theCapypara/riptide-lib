"""
Functions for processing ``config`` entries in :class:`riptide.config.document.service.Service` objects
"""
import os
from functools import partial
from typing import TYPE_CHECKING

from jinja2 import Environment

from riptide.config.files import get_project_meta_folder, remove_all_special_chars
from riptide.config.service.config_files_helper_functions import read_file

if TYPE_CHECKING:
    from riptide.config.document.service import Service

FOLDER_FOR_PROCESSED_CONFIG = 'processed_config'
jinja2env = Environment()


def process_config(config_name: str, config: dict, service: 'Service') -> str:
    """
    Processes the config file for the given project.

    Since project files can contain Jinja2 templating, variables are first resolved using configcrunch.

    The resulting file is written to the project's meta folder (_riptide) and this file is then mounted
    to the requested path inside the container

    :param service: The service that the config entry comes from.
    :param config: The actual config entry as specified in the Service schema.
    :param config_name: Name of the config entry
    :return: Path to the processed config file.
    """
    if not os.path.exists(config["$source"]) or not os.path.isfile(config["$source"]):
        raise ValueError(
            f"Configuration file {config['$source']}, specified by {config['from']} in service {service['$name']} "
            f"does not exist or is not a file. This probably happens because one of your services has an invalid "
            f"setting for the 'config' entries."
        )

    target_file = get_config_file_path(config_name, service)

    # Additional helper functions
    read_file_partial = partial(read_file, config["$source"])
    read_file_partial.__name__ = read_file.__name__

    with open(config["$source"], 'r') as stream:
        processed_file = service.process_vars_for(stream.read(), [
            read_file_partial
        ])

    # Weird Docker bug: The file has to exist in the actual code directory
    # as well, otherwise strange things happen. Create the file and add a notice
    if config['to'].startswith('/src/') and 'roles' in service and 'src' in service['roles']:
        relative_to = config['to'][5:]
        config_in_project_src = os.path.join(service.parent().parent().src_folder(), relative_to)
        if not os.path.isfile(config_in_project_src):
            # Create the directories of the dummy file as well, in case they don't exist.
            os.makedirs(os.path.dirname(config_in_project_src), exist_ok=True)
            with open(config_in_project_src, 'w') as f:
                f.writelines([
                    f'#!/bin/false -- This file was created by Riptide. It is not actually used. '
                    f'In the service container the file {target_file} is mounted here instead. That file is auto-'
                    f'generated based on the file {config["$source"]}.'
                ])

    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    with open(target_file, 'w') as f:
        f.write(processed_file)

    return target_file


def get_config_file_path(config_name: str, service: 'Service') -> str:
    """
    Returns the path to the processed configuration file for a service.

    :param config_name: Name of the config entry
    :param service: Service object that the config entry belongs to
    :return: Path to the processed config file, might not exist yet.
    """
    project = service.get_project()
    processed_config_folder = os.path.join(
        get_project_meta_folder(project.folder()),
        FOLDER_FOR_PROCESSED_CONFIG,
        service["$name"]
    )
    target_file = os.path.join(
        processed_config_folder,
        remove_all_special_chars(config_name)
    )

    return target_file
