"""
Functions for processing ``config`` entries in :class:`riptide.config.document.service.Service` objects
"""
import os
from typing import TYPE_CHECKING

from riptide.config.files import get_project_meta_folder, remove_all_special_chars

if TYPE_CHECKING:
    from riptide.config.document.service import Service

FOLDER_FOR_PROCESSED_CONFIG = 'processed_config'


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
            "Configuration file %s, specified by %s in service %s does not exist or is not a file."
            "This probably happens because one of your services has an invalid setting for the 'config' entries."
            % (config["$source"], config["from"], service["$name"])
        )

    target_file = get_config_file_path(config_name, service)

    with open(config["$source"], 'r') as stream:
        processed_file = service.process_vars_for(stream.read())

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
