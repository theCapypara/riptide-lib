import warnings
from collections import OrderedDict

import tempfile
from pathlib import PurePath
from typing import List, TYPE_CHECKING

from schema import Schema, Optional, Or

from configcrunch import YamlConfigDocument, ConfigcrunchError
from configcrunch.abstract import variable_helper
from riptide.config.errors import RiptideDeprecationWarning
from riptide.config.files import CONTAINER_SRC_PATH, CONTAINER_HOME_PATH
from riptide.config.service.config_files import *
from riptide.config.service.logging import *

# todo: validate actual schema values -> better schema | ALL documents
from riptide.config.service.ports import get_additional_port
from riptide.config.service.volumes import process_additional_volumes
from riptide.db.driver import db_driver_for_service
from riptide.engine.abstract import RIPTIDE_HOST_HOSTNAME
from riptide.lib.cross_platform import cppath
from riptide.lib.cross_platform.cpuser import getuid, getgid

DOMAIN_PROJECT_SERVICE_SEP = "--"

if TYPE_CHECKING:
    from riptide.config.document.project import Project

HEADER = 'service'


class Service(YamlConfigDocument):
    """
    A service document. Represents the definition and specification for a running service container.

    Placed inside an :class:`riptide.config.document.app.App`.

    The name of the service comes from the key it is assigned in the app. This key is added to
    the service with the ``$name`` entry during runtime.

    Example::

        service:
          image: hello/world:blubbel
          port: 8080

    """
    def __init__(
            self,
            document: dict,
            path: str = None,
            parent: 'YamlConfigDocument' = None,
            already_loaded_docs: List[str] = None,
            absolute_paths=None
    ):
        self._db_driver = None
        self._loaded_port_mappings = None
        super().__init__(document, path, parent, already_loaded_docs, absolute_paths)

    @classmethod
    def header(cls) -> str:
        return HEADER

    def schema(self) -> Schema:
        return Schema(
            {
                Optional('$ref'): str,  # reference to other Service documents
                Optional('$name'): str,  # Added by system during processing parent app.
                Optional('roles'): [str],
                'image': str,
                Optional('command'): str,
                Optional('port'): int,
                Optional('logging'): {
                    Optional('stdout'): bool,
                    Optional('stderr'): bool,
                    Optional('paths'): {str: str},
                    Optional('commands'): {str: str}
                },
                Optional('pre_start'): [str],
                Optional('post_start'): [str],
                Optional('environment'): {str: str},
                Optional('config'): {
                    str: {
                        'from': str,
                        '$source': str,  # Path to the document that "from" references. Is added durinng loading of service
                        'to': str
                    }
                },
                # Whether to run as the user using riptide (True) or image default (False). Default: True
                # Limitation: If false and the image USER is not root,
                #             then a user with the id of the image USER must exist in /etc/passwd of the image.
                Optional('run_as_current_user'): bool,
                # DEPRECATED. Inverse of run_as_current_user if set
                Optional('run_as_root'): bool,
                # Whether to create the riptide user and group, mapped to current user. Default: False
                Optional('dont_create_user'): bool,
                Optional('working_directory'): str,
                Optional('additional_ports'): {
                    str: {
                        'title': str,
                        'container': int,
                        'host_start': int
                    }
                },
                Optional('additional_volumes'): {
                    str: {
                        'host': str,
                        'container': str,
                        Optional('mode'): Or('rw', 'ro')  # default: rw - can be rw/ro.
                    }
                },
                # db only
                Optional('driver'): {
                    'name': str,
                    'config': any  # defined by driver
                }
            }
        )

    def _initialize_data_after_merge(self):
        """
        Initializes non-set fields, initiliazes the database
        driver and creates all files for ``config`` entries.
        """
        if "run_as_root" in self:
            warnings.warn(
                "Deprecated key run_as_root = %r in a service found. Please replace with run_as_current_user = %r." %
                (self.doc["run_as_root"], not self.doc["run_as_root"]),
                RiptideDeprecationWarning
            )
            self.doc["run_as_current_user"] = not self.doc["run_as_root"]
        if "run_as_current_user" not in self:
            self.doc["run_as_current_user"] = True

        if "dont_create_user" not in self:
            self.doc["dont_create_user"] = False

        if "pre_start" not in self:
            self.doc["pre_start"] = []

        if "post_start" not in self:
            self.doc["post_start"] = []

        if "roles" not in self:
            self.doc["roles"] = []

        if "db" in self["roles"]:
            self._db_driver = db_driver_for_service.get(self)
            if self._db_driver:
                # Collect additional ports for the db driver
                my_original_ports = self["additional_ports"] if "additional_ports" in self else {}
                db_ports = self._db_driver.collect_additional_ports()
                self["additional_ports"] = db_ports.copy()
                self["additional_ports"].update(my_original_ports)

        # Load the absolute path of the config documents specified in config[]["from"]
        if self.absolute_paths:
            folders_to_search = [os.path.dirname(path) for path in self.absolute_paths]
        else:
            try:
                folders_to_search = [self.get_project().folder()]
            except IndexError:
                # Fallback: Assume cwd
                folders_to_search = [os.getcwd()]

        if "config" in self and isinstance(self["config"], dict):
            for config in self["config"].values():
                # TODO: Currently doesn't allow . or os.sep at the beginning for security reasons.
                if config["from"].startswith(".") or config["from"].startswith(os.sep):
                    raise ConfigcrunchError("Config 'from' items in services may not start with . or %s." % os.sep)

                config["$source"] = None
                for folder in folders_to_search:
                    path_to_config = os.path.join(folder, config["from"])
                    if os.path.exists(path_to_config):
                        config["$source"] = path_to_config
                        break
                if config["$source"] is None:
                    # Did not find the file at any of the possible places
                    raise ConfigcrunchError(
                        "Configuration file '%s' in service at '%s' does not exist or is not a file. "
                        "This propably happens because one of your services has an invalid setting for the 'config' entries. "
                        "Based on how the configuration was merged, the following places were searched: %s"
                        % (config["from"], self.absolute_paths[0] if self.absolute_paths else '???', str(folders_to_search))
                    )

    def _initialize_data_after_variables(self):
        """
        Normalizes all host-paths to only use the system-type directory separator.
        """
        if "additional_volumes" in self:
            for obj in self.doc["additional_volumes"].values():
                obj["host"] = cppath.normalize(obj["host"])
        if "config" in self:
            for obj in self.doc["config"].values():
                obj["$source"] = cppath.normalize(obj["$source"])

    def validate(self) -> bool:
        """ Validates the Schema and if a database driver is defined, validates that the driver is installed. """
        if not super().validate():
            return False

        # Db Driver constraints. If role db is set, a "driver" has to be set and code has to exist for it.
        if "roles" in self and "db" in self["roles"]:
            if "driver" not in self or self._db_driver is None:
                raise ConfigcrunchError("Service %s validation: If a service has the role 'db' it has to have a valid "
                                        "'driver' entry with a driver that is available." % self["$name"])
            self._db_driver.validate_service()
        return True

    def before_start(self):
        """Loads data required for service start, called by riptide_project_start_ctx()"""
        # Collect ports
        project = self.get_project()
        self._loaded_port_mappings = {}

        if "additional_ports" in self:
            for port_request in self["additional_ports"].values():
                self._loaded_port_mappings[port_request["container"]] = get_additional_port(project, self,
                                                                                            port_request["host_start"])

        # Create working_directory if it doesn't exist and it is relative
        if "working_directory" in self and not PurePosixPath(self["working_directory"]).is_absolute():
            os.makedirs(os.path.join(
                self.get_project().folder(),
                self.get_project()["src"],
                self["working_directory"]
            ), exist_ok=True)

    def get_project(self) -> 'Project':
        """
        Returns the project or raises an error if this is not assigned to a project

        :raises: IndexError: If not assigned to a project
        """
        try:
            return self.parent_doc.parent_doc
        except Exception as ex:
            raise IndexError("Expected service to have a project assigned") from ex

    def collect_volumes(self) -> OrderedDict:
        """
        Collect volume mappings that this service should be getting when running.

        Volumes are built from following sources:

        * Source code is mounted as volume if role "src" is set
        * Config entries are compiled using Jinja and mounted to their paths
        * Logging files/streams are put into the _riptide/logs folder.
        * If role "db" is set, and a database driver is found, it's volumes are added
        * additional_volumes are added.

        Also creates/updates necessary files and folders
        (eg. compiled configuration, logging).

        :return: dict. Return format is the docker container API volumes dict format.
                       See: https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run
        """
        project = self.get_project()
        volumes = OrderedDict({})

        # role src
        if "src" in self["roles"]:
            volumes[project.src_folder()] = {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'}

        # config
        if "config" in self:
            for config_name, config in self["config"].items():
                volumes[process_config(config_name, config, self)] = {'bind': config["to"], 'mode': 'rw'}

        # logging
        if "logging" in self:
            create_logging_path(self)
            if "stdout" in self["logging"] and self["logging"]["stdout"]:
                volumes[get_logging_path_for(self, 'stdout')] = {'bind': LOGGING_CONTAINER_STDOUT, 'mode': 'rw'}
            if "stderr" in self["logging"] and self["logging"]["stderr"]:
                volumes[get_logging_path_for(self, 'stderr')] = {'bind': LOGGING_CONTAINER_STDERR, 'mode': 'rw'}
            if "paths" in self["logging"]:
                for name, path in self["logging"]["paths"].items():
                    logging_host_path = get_logging_path_for(self, name)
                    volumes[logging_host_path] = {'bind': path, 'mode': 'rw'}
            if "commands" in self["logging"]:
                for name in self["logging"]["commands"].keys():
                    logging_host_path = get_logging_path_for(self, name)
                    logging_command_stdout = get_command_logging_container_path(name)
                    volumes[logging_host_path] = {'bind': logging_command_stdout, 'mode': 'rw'}

        # db driver
        if self._db_driver:
            db_driver_volumes = self._db_driver.collect_volumes()
            for vol in db_driver_volumes.keys():
                # Create db driver volumes as directories if they don't exist yet
                os.makedirs(vol, exist_ok=True)
            volumes.update(db_driver_volumes)

        # additional_volumes
        if "additional_volumes" in self:
            volumes.update(process_additional_volumes(list(self['additional_volumes'].values()), project.folder()))

        return volumes

    def collect_environment(self) -> dict:
        """
        Collect environment variables from the "environment" entry in the service
        configuration.

        :return: dict. Returned format is ``{key1: value1, key2: value2}``.
        """
        env = {}
        if "environment" in self:
            for name, value in self["environment"].items():
                env[name] = value

        # db driver
        if self._db_driver:
            env.update(self._db_driver.collect_environment())

        return env

    def collect_ports(self) -> dict:
        """
        Takes additional_ports and returns the actual host/container mappings for these
        ports.

        The resulting host parts are system-unique, so Riptide will not assign
        a port twice across multiple projects/services.

        To achieve this, port bindings are saved into $CONFIG_DIR/ports.json.

        :return: dict. Returned format is {port_service1: port_host1, port_service2: port_host2}
        """
        # This is already loaded in before_start. Make sure to use riptide_start_project_ctx
        # when starting if this is None
        return self._loaded_port_mappings

    @variable_helper
    def volume_path(self) -> str:
        """Returns the path to a service-unique directory for storing container data."""
        path = os.path.join(get_project_meta_folder(self.get_project().folder()), 'data', self["$name"])
        return path

    @variable_helper
    def get_working_directory(self) -> str:
        """Returns the path to the working directory of the service **inside** the container."""
        workdir = None if "src" not in self["roles"] else CONTAINER_SRC_PATH
        if "working_directory" in self:
            if PurePosixPath(self["working_directory"]).is_absolute():
                return self["working_directory"]
            elif workdir is not None:
                return str(PurePosixPath(workdir).joinpath(self["working_directory"]))
        return workdir

    @variable_helper
    def domain(self):
        """Returns the full domain name that this service should be available under, without protocol."""
        if "main" in self["roles"]:
            return self.get_project()["name"] + "." + self.parent_doc.parent_doc.parent_doc["proxy"]["url"]
        return self.get_project()["name"] + DOMAIN_PROJECT_SERVICE_SEP + self["$name"] + "." + self.parent_doc.parent_doc.parent_doc["proxy"]["url"]

    @variable_helper
    def os_user(self) -> str:
        """Returns the user id of the current user as string (or 0 under Windows)."""
        return str(getuid())

    @variable_helper
    def os_group(self) -> str:
        """Returns the user id of the current user's primary group as string (or 0 under Windows)."""
        return str(getgid())

    @variable_helper
    def host_address(self) -> str:
        """Returns the hostname that the host system is reachable under inside the container."""
        return RIPTIDE_HOST_HOSTNAME

    @variable_helper
    def home_path(self) -> str:
        """Returns the path to the home directory inside the container."""
        return CONTAINER_HOME_PATH

    @variable_helper
    def config(self, config_name: str) -> str:
        """
        Returns the (host)-path to a config-entry of this service, for use in other services.

        The config file will be processed as it would normally, all variables in it will be resolved relative to this
        service.
        :type config_name: Key of the entry in this service's ``config`` map.
        """
        if "config" in self and config_name in self["config"]:
            return process_config(config_name, self["config"][config_name], self)
        raise FileNotFoundError("Config %s for service %s not found"
                                % (config_name, self["$name"] if "$name" in self else "???"))

    @variable_helper
    def get_tempdir(self) -> str:
        """ Returns the path to the system tempoary directory where the user (should) have write access."""
        return tempfile.gettempdir()
