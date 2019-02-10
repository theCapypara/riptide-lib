"""Functions for helping processing 'config' entries in service objects"""
import os

from riptide.config.files import get_project_meta_folder, remove_all_special_chars

FOLDER_FOR_PROCESSED_CONFIG = 'processed_config'


def process_config(config, service):
    """
    Processes the config file for the given project.
    Since project files can contain Jinja2 templating, variables are first resolved using configcrunch.
    The resulting file is written to the project's meta folder (_riptide) and this file is then mounted
    to the requested path inside the container
    """
    if not os.path.exists(config["$source"]) or not os.path.isfile(config["$source"]):
        raise ValueError(
            "Configuration file %s, specified by %s in service %s does not exist or is not a file."
            "This propably happens because one of your services has an invalid setting for the 'config' entries."
            % (config["$source"], config["from"], service["$name"])
        )

    target_file = get_config_file_path(config["from"], service)

    with open(config["$source"], 'r') as stream:
        processed_file = service.process_vars_for(stream.read())

    try:
        os.makedirs(os.path.dirname(target_file))
    except FileExistsError:
        pass # Already exists, we don't care.

    with open(target_file, 'w') as f:
        f.write(processed_file)

    return target_file


def get_config_file_path(config_from, service):
    project = service.get_project()
    processed_config_folder = os.path.join(
        get_project_meta_folder(project.folder()),
        FOLDER_FOR_PROCESSED_CONFIG,
        service["$name"]
    )
    target_file = os.path.join(
        processed_config_folder,
        remove_all_special_chars(config_from)
    )

    return target_file
