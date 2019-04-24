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
    from riptide.config.document.app import App

HEADER = 'service'


class Service(YamlConfigDocument):
    """
    A service document. Represents the definition and specification for a running service container.

    Placed inside an :class:`riptide.config.document.app.App`.

    The name of the service comes from the key it is assigned in the app. This key is added to
    the service with the ``$name`` entry during runtime.

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
        """
        [$name]: str
            Name as specified in the key of the parent app.

            Added by system. DO NOT specify this yourself in the YAML files.

        [roles]: List[str]
            A list of roles for this service. You can use arbitrary strings and get services by their
            assigned roles using :func:`~riptide.config.document.app.App.get_service_by_role`.

            Some roles are pre-defined and have a special meaning:

                *main*:
                    This service is the main service for the app.

                    Some commands will default to this service and the proxy URL for this service is shorter.
                    Usually services are accessible via ``http://<project_name>--<service_name>.<proxy_url>``,
                    however the main service is accessible via ``http://<project_name>.<proxy_url>``.

                    Only one service is allowed to have this role.
                *src*:
                    The container of this service will have access to the source code of the application.

                    It's working directory will be set accordingly.
                *db*:
                    This service is the primary database. A database driver has to be set (see key ``driver``).

                    This service is then used by Riptide for `database management </user_docs/db.html>`.

        image: str
            Docker Image to use

        [command]: str
            Command to run inside of the container. Default's to command defined in image.

            .. warning:: Avoid quotes (", ') inside of the command, as those may lead to strange side effects.

        [port]: int
            HTTP port that the web service is accessible under. This port will be used by the proxy server to redirect
            the traffic.

            If the port is not specified, the service is not accessible via proxy server.

        [logging]
            Logging settings. All logs will be placed inside the "_riptide/logs" directory.

            [stdout]: bool
                Whether or not to log the stdout stream of the container's main command. Default: false
            [stderr]: bool
                Whether or not to log the stderr stream of the container's main command. Default: false
            [paths]
                {key}: str
                    Additional text files to mount into the logging directory. Keys are filename's on host (without .log)
                    and values are the paths inside the containers.
            [commands]
                {key}: str
                    Additional commands to start inside the container. Their stdout and stderr will be logged to the file
                    specified by the key.

        [pre_start]: List[str]
            List of commands to run, before the container starts. They are run sequentially.
            The startup will wait for the commands to finish. Exit codes (failures) are ignored.

            Each of these commands is run in a separate container based on the service specification. Each command
            is run in a "sh" shell.

        [post_start]: List[str]
            List of commands to run, after container starts. They are run sequentially.
            The startup will wait for the commands to finish. Exit codes (failures) are ignored.

            Each of these command's is run inside the service container (equivalent of ``docker exec``).
            Each command is run in a “sh” shell.

        [environment]
            Additional environment variables

            {key}: str
                Key is the name of the variable, value is the value.

        [working_directory]: str
            Working directory for the service, either

            - absolute, if an absolute path is given
            - relative to the src specified in the project, if the role "src" is set.
            - relative to the default working directory from the image, if the role is not set.

            Defaults to ``.``.

        [config]
            Additional configuration files to mount. These files are NOT directly mounted.
            Instead they are processed and the resulting file is mounted.

            All variables and variable helpers inside the configuration file are processed.

            Example configuration file (demo.ini)::

                [demo]
                domain={{domain()}}
                project_name={{parent().parent().name}}

            Resulting file that will be mounted::

                [demo]
                domain=projectname.riptide.local
                project_name=projectname

            {key}
                from: str
                    Path to the configuration file, relative to any YAML file that was used
                    to load the project (including "riptide.yml" and all yaml files used inside the repository;
                    all are searched). Absolute paths are not allowed.

                to: str
                    Path to store the configuration file at, relative to working directory of container or absolute.

        [additional_ports]
            Additional TCP and/or UDP ports that will be made available on the host system.
            For details see section in
            `user guide </user_docs/7_working_with_riptide.html#access-other-tcp-udp-ports>`_.

            {key}
                title: str
                    Title for this port, will be displayed in ``riptide status``

                container: int
                    Port number inside the container

                host_start: int
                    First port number on host that Riptide will try to reserve, if the
                    port is already occupied, the next one will be used. This port
                    will be reserved and permanently used for this service after that.

        [additional_volumes]
            Additional volumes to mount into the container for this command.

            {key}
                host: str
                    Path on the host system to the volume. Avoid hardcoded absolute paths.
                container: str
                    Path inside the container (relative to src of Project or absolute).
                [mode]: str
                    Whether to mount the volume read-write ("rw", default) or read-only ("ro").

        [driver]
            The database driver configuration, set this only if the role "db" is set.

            Detailed documentation can be found in a `separate section </config_docs/database_drivers.html>`_.

            name: str
                Name of the database driver, must be installed.
            config: ???
                Specification depends on the database driver.

        [run_as_current_user]: bool
            Whether to run as the user using riptide (True)
            or image default (False).

            Default: True

            Riptide will always create the user and group, matching the host user and group,
            inside the container on startup, regardless of this setting.

            Some images don't support switching the user, set this to false then.
            Please note that, if you set this to false and also specify the role 'src', you may run
            into permission issues.

        **Example Document:**

        .. code-block:: yaml

            service:
              image: node:10
              roles:
                - main
                - src
              command: 'node server.js'
              port: 1234
              logging:
                stdout: true
                stderr: false
                paths:
                  one: '/foo/bar'
                commands:
                  two: 'varnishlog'
              pre_start:
                - "echo 'command 1'"
                - "echo 'command 2'"
              post_start:
                - "echo 'command 3'"
                - "echo 'command 4'"
              environment:
                SOMETHING_IMPORTANT: foo
              config:
                one:
                  from: ci/config.yml
                  to: app_config/config.yml
              working_directory: www
              additional_ports:
                one:
                  title: MySQL Port
                  container: 3306
                  host_start: 3006
              additional_volumes:
                temporary_files:
                  host: '{{ get_tempdir() }}'
                  container: /tmp

        """
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
                # sanity check if from and to are in this config entry, if not it's invalid.
                # the validation will catch this later
                if "from" not in config or "to" not in config:
                    continue

                # Doesn't allow . or os.sep at the beginning for security reasons.
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
                        "This probably happens because one of your services has an invalid setting for the 'config' entries. "
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

    def error_str(self) -> str:
        return "%s<%s>" % (self.__class__.__name__, self["$name"] if "$name" in self else "???")

    @variable_helper
    def parent(self) -> 'App':
        """
        Returns the app that this service belongs to.

        Example usage::

            something: '{{ parent().notices.usage }}'

        Example result::

            something: 'This is easy to use.'
        """
        # noinspection PyTypeChecker
        return super().parent()

    @variable_helper
    def volume_path(self) -> str:
        """
        Returns the (host) path to a service-unique directory for storing container data.

        Example usage::

            additional_volumes:
                cache:
                    host: '{{ volume_path() }}/cache'
                    container: '/foo/bar/cache'

        Example result::

            additional_volumes:
                cache:
                    host: '/home/peter/my_projects/project1/_riptide/data/service_name/cache'
                    container: '/foo/bar/cache'
        """
        path = os.path.join(get_project_meta_folder(self.get_project().folder()), 'data', self["$name"])
        return path

    @variable_helper
    def get_working_directory(self) -> str:
        """
        Returns the path to the working directory of the service **inside** the container.

        .. warning:: Does not work as expected for services started via "start-fg".

        Example usage::

            something: '{{ get_working_directory() }}'

        Example result::

            something: '/src/working_dir'
        """
        workdir = None if "src" not in self["roles"] else CONTAINER_SRC_PATH
        if "working_directory" in self:
            if PurePosixPath(self["working_directory"]).is_absolute():
                return self["working_directory"]
            elif workdir is not None:
                return str(PurePosixPath(workdir).joinpath(self["working_directory"]))
        return workdir

    @variable_helper
    def domain(self) -> str:
        """
        Returns the full domain name that this service should be available under, without protocol. This is the
        same domain as used for the proxy server.

        Example usage::

            something: 'https://{{ domain() }}'

        Example result::

            something: 'https://project--service.riptide.local'
        """
        if "main" in self["roles"]:
            return self.get_project()["name"] + "." + self.parent_doc.parent_doc.parent_doc["proxy"]["url"]
        return self.get_project()["name"] + DOMAIN_PROJECT_SERVICE_SEP + self["$name"] + "." + self.parent_doc.parent_doc.parent_doc["proxy"]["url"]

    @variable_helper
    def os_user(self) -> str:
        """
        Returns the user id of the current user as string (or 0 under Windows).

        This is the same id that would be used if "run_as_current_user" was set to `true`.

        Example usage::

            something: '{{ os_user() }}'

        Example result::

            something: '1000'
        """
        return str(getuid())

    @variable_helper
    def os_group(self) -> str:
        """
        Returns the id of the current user's primary group as string (or 0 under Windows).

        This is the same id that would be used if "run_as_current_user" was set to `true`.

        Example usage::

            something: '{{ os_group() }}'

        Example result::

            something: '100'
        """
        return str(getgid())

    @variable_helper
    def host_address(self) -> str:
        """
        Returns the hostname that the host system is reachable under inside the container.

        Example usage::

            something: '{{ host_address() }}'

        Example result::

            something: 'host.riptide.internal'
        """
        return RIPTIDE_HOST_HOSTNAME

    @variable_helper
    def home_path(self) -> str:
        """
        Returns the path to the home directory inside the container.

        Example usage::

            something: '{{ home_path() }}'

        Example result::

            something: '/home/riptide'
        """
        return CONTAINER_HOME_PATH

    @variable_helper
    def config(self, config_name: str) -> str:
        """
        Returns the (host)-path to a config-entry of this service, for use in other services.

        The config file will be processed as it would normally, all variables in it will be resolved relative to this
        service.

        This allows you, for example, to use service configuration files for commands (as shown below).

        Example usage::

            app:
                name: demo
                services:
                    service:
                        image: riptidepy/example
                        config:
                            example_config:
                                from: 'foo.yml'
                                to: '/bar.yml'
                commands:
                    command:
                        image: riptidepy/example
                        additional_volumes:
                            example_config_for_command:
                                host: '{{ parent().services.service.config("example_config")}}'
                                container: '/bar.yml'


        Example result::

            app:
                name: demo
                services:
                    service:
                        image: riptidepy/example
                        config:
                            example_config:
                                from: 'foo.yml'
                                to: '/bar.yml'
                commands:
                    command:
                        image: riptidepy/example
                        additional_volumes:
                            example_config_for_command:
                                host: '/path/to/project/_riptide/processed_configs/service/example-config'
                                container: '/bar.yml'

        :param config_name: Key of the entry in this service's ``config`` map.
        """
        if "config" in self and config_name in self["config"]:
            return process_config(config_name, self["config"][config_name], self)
        raise FileNotFoundError("Config %s for service %s not found"
                                % (config_name, self["$name"] if "$name" in self else "???"))

    @variable_helper
    def get_tempdir(self) -> str:
        """
        Returns the path to the system (host!) temporary directory where the user (should) have write access.

        Example usage::

            something: '{{ get_tempdir() }}'

        Example result::

            something: '/tmp'
        """
        return tempfile.gettempdir()
