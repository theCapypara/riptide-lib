"""
Functions for processing ``config`` entries in :class:`riptide.config.document.service.Service` objects
"""
import os
from functools import partial
from typing import TYPE_CHECKING, Dict

from riptide.config.files import get_project_meta_folder, remove_all_special_chars
from riptide.config.service.config_files_helper_functions import read_file

if TYPE_CHECKING:
    from riptide.config.document.service import Service

FOLDER_FOR_PROCESSED_CONFIG = 'processed_config'


def process_config(
        volumes: Dict, config_name: str, config: dict, service: 'Service', bind_path: str, regenerate=True
) -> None:
    """
    Processes the config file for the given project.

    Since project files can contain Jinja2 templating, variables are first resolved using configcrunch.

    The resulting file is written to the project's meta folder (_riptide) and this file is then mounted
    to the requested path inside the container.

    Modifies the volume list "volumes" and adds a new volume entry.

    If regenerate is False, and the generated config file already exists, it is not regenerated.

    If bind_path is relative to the container project src path ("/src") and the service has the role
    "src", the file is NOT written to _riptide but instead to the specified path directly in the project.
    No volume is added in this case! The file will be avaiable via the "src" mount!

    :param volumes: The volume list to modify, in Service.collect_volumes format
    :param service: The service that the config entry comes from.
    :param config: The actual config entry as specified in the Service schema.
    :param config_name: Name of the config entry
    :param bind_path: The container bind path
    :param regenerate: Whether to regenerate the file if it already exists
    """
    if not os.path.exists(config["$source"]) or not os.path.isfile(config["$source"]):
        raise ValueError(
            f"Configuration file {config['$source']}, specified by {config['from']} in service {service['$name']} "
            f"does not exist or is not a file. This probably happens because one of your services has an invalid "
            f"setting for the 'config' entries."
        )

    is_in_source_path = bind_path.startswith('/src/') and 'roles' in service and 'src' in service['roles']

    target_file = get_config_file_path(config_name, service, is_in_source_path, bind_path)
    if regenerate or not os.path.exists(target_file):
        # Additional helper functions
        read_file_partial = partial(read_file, config["$source"])
        read_file_partial.__name__ = read_file.__name__

        with open(config["$source"], 'r') as stream:
            processed_file = service.process_vars_for(stream.read(), [
                read_file_partial
            ])

        if is_in_source_path:
            notice_file = target_file + '.riptide_info.txt'
            if not os.path.isfile(notice_file):
                with open(notice_file, 'w') as f:
                    f.writelines([
                        f'The file {os.path.basename(target_file)} was created by Riptide. Do not modify it.\n'
                        f'It will automatically be re-generated if you restart the project.\n'
                        f'Please add this file and {os.path.basename(target_file)} to the ignore file of your VCS.\n\n'
                        f'The {os.path.basename(target_file)} is based on a template file, which you can find here:\n'
                        f'   {config["$source"]}\n\n'
                        f'Please have a look at the documentation if you want to use a different template file (Schema for '
                        f'Services, entry "config").'
                    ])

        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        with open(target_file, 'w') as f:
            f.write(processed_file)

    # Only add a volume if needed
    if not is_in_source_path:
        volumes[target_file] = {
           'bind': bind_path, 'mode': 'rw'
        }


def get_config_file_path(config_name: str, service: 'Service', is_in_source_path: bool, bind_path: str) -> str:
    """
    Returns the path to the processed configuration file for a service.

    :param config_name: Name of the config entry
    :param service: Service object that the config entry belongs to
    :return: Path to the processed config file, might not exist yet.
    """
    if is_in_source_path:
        # FILE INSIDE SOURCE: Copy to src!
        return os.path.join(service.get_project().src_folder(), bind_path[len('/str/'):])
    else:
        # FILE IN _RIPTIDE:
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
