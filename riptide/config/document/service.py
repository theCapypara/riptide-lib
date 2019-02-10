from typing import List

from schema import Schema, Optional

from configcrunch import YamlConfigDocument
from configcrunch.abstract import variable_helper
from riptide.config.files import CONTAINER_SRC_PATH, CONTAINER_HOME_PATH
from riptide.config.service.config_files import *
from riptide.config.service.logging import *

# todo: validate actual schema values -> better schema | ALL documents
from riptide.config.service.ports import get_additional_port
from riptide.db.driver import db_driver_for_service
from riptide.engine.abstract import RIPTIDE_HOST_HOSTNAME
from riptide.lib.cross_platform import cppath
from riptide.lib.cross_platform.cpuser import getuid, getgid


class Service(YamlConfigDocument):

    def __init__(
            self,
            document: dict,
            path: str = None,
            parent: 'YamlConfigDocument' = None,
            already_loaded_docs: List[str] = None
    ):
        self._db_driver = None
        self._loaded_port_mappings = None
        super().__init__(document, path, parent, already_loaded_docs)

    def _initialize_data(self):
        """ Load the absolute path of the config documents specified in config[]["from"]"""
        if self.path:
            folder_of_self = os.path.dirname(self.path)
        else:
            folder_of_self = self.get_project().folder()

        if "config" in self:
            for config in self["config"]:
                # TODO: Currently doesn't allow . or os.sep at the beginning for security reasons.
                if config["from"].startswith(".") or config["from"].startswith(os.sep):
                    raise ValueError("Config 'from' items in services may not start with . or %s." % os.sep)
                config["$source"] = os.path.join(folder_of_self, config["from"])

        if "run_as_root" not in self:
            self.doc["run_as_root"] = False

        if "dont_create_user" not in self:
            self.doc["dont_create_user"] = False

        if "pre_start" not in self:
            self.doc["pre_start"] = []

        if "post_start" not in self:
            self.doc["post_start"] = []

        if "roles" not in self:
            self.doc["roles"] = []

        if "additional_ports" not in self:
            self.doc["additional_ports"] = []

        if "db" in self["roles"]:
            self._db_driver = db_driver_for_service.get(self)
            if self._db_driver:
                # Collect additional ports for the db driver
                self["additional_ports"] += self._db_driver.collect_additional_ports()

    def validate(self) -> bool:
        if not super().validate():
            return False

        # Db Driver constraints. If role db is set, a "driver" has to be set and code has to exist for it.
        if "db" in self["roles"]:
            if "driver" not in self or self._db_driver is None:
                raise ValueError("Service %s validation: If a service has the role 'db' it has to have a valid "
                                 "'driver' entry with a driver that is available." % self["$name"])
            self._db_driver.validate_service()

    def process_vars(self) -> 'YamlConfigDocument':
        # todo needs to happen after variables have been processed, but we need a cleaner callback for this
        super().process_vars()

        # Normalize all host-paths to only use the system-type directory separator
        if "additional_volumes" in self:
            for obj in self.doc["additional_volumes"]:
                obj["host"] = cppath.normalize(obj["host"])
        if "config" in self:
            for obj in self.doc["config"]:
                obj["$source"] = cppath.normalize(obj["$source"])

        return self

    def before_start(self):
        """Load data required for service start, called by riptide_project_start_ctx()"""
        # Collect ports
        project = self.get_project()
        self._loaded_port_mappings = {}

        for port_request in self["additional_ports"]:
            self._loaded_port_mappings[port_request["container"]] = get_additional_port(project, self, port_request["host_start"])

    @classmethod
    def header(cls) -> str:
        return "service"

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
                Optional('config'): [
                    {
                        'from': str,
                        '$source': str,  # Path to the document that "from" references. Is added durinng loading of service
                        'to': str
                    }
                ],
                # Whether to run as user using riptide or root. Default: False
                Optional('run_as_root'): bool,
                # Whether to create the riptide user and group, mapped to current user. Default: False
                Optional('dont_create_user'): bool,
                Optional('working_directory'): str,
                Optional('additional_ports'): [
                    {
                        'title': str,
                        'container': int,
                        'host_start': int
                    }
                ],
                Optional('additional_volumes'): [
                    {
                        'host': str,
                        'container': str,
                        Optional('mode'): str  # default: rw - can be rw/ro.
                    }
                ],
                # db only
                Optional('driver'): {
                    'name': str,
                    'config': any  # defined by driver
                }
            }
        )

    def get_project(self):
        try:
            return self.parent_doc.parent_doc
        except Exception as ex:
            raise IndexError("Expected service to have a project assigned") from ex

    def collect_volumes(self):
        """
        Collect volume mappings that this service should be getting when running.
        Volumes are built from following sources:
        - Source code is mounted as volume if role "src" is set
        - Config entries are compiled using Jinja and mounted to their paths
        - Logging files/streams are put into the _riptide/logs folder.
        - If role "db" is set, and a database driver is found, it's volumes are added
        - additional_volumes are added.

        Also creates/updates necessary files and folders
        (eg. compiled configuration, logging).

        Return format is the docker container API volumes dict format.
        See: https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run
        """
        project = self.get_project()
        volumes = {}

        # role src
        if "src" in self["roles"]:
            volumes[project.src_folder()] = {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'}

        # config
        if "config" in self:
            for config in self["config"]:
                volumes[process_config(config, self)] = {'bind': config["to"], 'mode': 'rw'}  # todo: ro default

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
            for vol in self["additional_volumes"]:
                # ~ paths
                if vol["host"][0] == "~":
                    vol["host"] = os.path.expanduser("~") + vol["host"][1:]
                # Relative paths
                if not os.path.isabs(vol["host"]):
                    vol["host"] = os.path.join(project.folder(), vol["host"])

                mode = vol["mode"] if "mode" in vol else "rw"
                volumes[vol["host"]] = {'bind': vol["container"], 'mode': mode}
                # Create additional volumes as directories if they don't exist yet
                os.makedirs(vol["host"], exist_ok=True)

        return volumes

    def collect_environment(self):
        """
        Collect environment variables from the "environment" entry in the service
        configuration.
        Returned format is {key1: value1, key2: value2}
        :return:
        """
        env = {}
        if "environment" in self:
            for name, value in self["environment"].items():
                env[name] = value

        # db driver
        if self._db_driver:
            env.update(self._db_driver.collect_environment())

        return env

    def collect_ports(self):
        """
        Takes additional_ports and returns the actual host/container mappings for these
        ports. The resulting host parts are system-unique, so Riptide will not assign
        a port twice across multiple projects/services.
        To achieve this, port bindings are saved into $CONFIG_DIR/ports.json.

        Returned format is {port_service1: port_host1, port_service2: port_host2}
        :return:
        """
        # This is already loaded in before_start. Make sure to use riptide_start_project_ctx
        # when starting if this is None
        return self._loaded_port_mappings

    @variable_helper
    def volume_path(self):
        """Returns the path to a service-unique directory for storing container data"""
        path = os.path.join(get_project_meta_folder(self.get_project().folder()), 'data', self["$name"])
        return path

    @variable_helper
    def get_working_directory(self):
        workdir = None if "src" not in self["roles"] else CONTAINER_SRC_PATH
        if "working_directory" in self:
            if PurePosixPath(self["working_directory"]).is_absolute():
                return self["working_directory"]
            elif workdir is not None:
                return str(PurePosixPath(workdir).joinpath(self["working_directory"]))
        return workdir

    @variable_helper
    def domain(self):
        if "main" in self["roles"]:
            return self.get_project()["name"] + "." + self.parent_doc.parent_doc.parent_doc["proxy"]["url"]
        return self.get_project()["name"] + "__" + self["$name"] + "." + self.parent_doc.parent_doc.parent_doc["proxy"]["url"]

    @variable_helper
    def os_user(self):
        return str(getuid())

    @variable_helper
    def os_group(self):
        return str(getgid())

    @variable_helper
    def host_address(self):
        """Returns the hostname that the host system is reachable under"""
        return RIPTIDE_HOST_HOSTNAME

    @variable_helper
    def home_path(self):
        return CONTAINER_HOME_PATH

    @variable_helper
    def config(self, from_path):
        """ TODO DOC """
        return get_config_file_path(from_path, self)
