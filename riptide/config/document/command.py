from collections import OrderedDict

import os
from pathlib import PurePosixPath

from dotenv import dotenv_values
from schema import Schema, Optional, Or
from typing import TYPE_CHECKING, Union

from configcrunch import variable_helper
from riptide.config.document.common_service_command import ContainerDefinitionYamlConfigDocument
from riptide.config.files import get_project_meta_folder, CONTAINER_SRC_PATH
from riptide.config.service.config_files import process_config
from riptide.config.service.volumes import process_additional_volumes
from riptide.lib.cross_platform import cppath

if TYPE_CHECKING:
    from riptide.config.document.project import Project
    from riptide.config.document.app import App


HEADER = 'command'
KEY_IDENTIFIER_IN_SERVICE_COMMAND = 'in_service_with_role'


class Command(ContainerDefinitionYamlConfigDocument):
    """
    A command document. Specifies a CLI command to be executable by the user.

    Placed inside an :class:`riptide.config.document.app.App`.

    """
    @classmethod
    def header(cls) -> str:
        return HEADER

    @classmethod
    def schema(cls) -> Schema:
        """
        Can be either a normal command, a command in a service, or an alias command.
        """
        return Schema(
            Or(cls.schema_alias(), cls.schema_normal(), cls.schema_in_service())
        )

    @classmethod
    def schema_normal(cls):
        """
        Normal commands are executed in seperate containers, that are running
        in the same container network as the services.

        [$name]: str
            Name as specified in the key of the parent app.

            Added by system. DO NOT specify this yourself in the YAML files.

        image: str
            Docker Image to use

        [command]: str
            Command to run inside of the container. Default's to command defined in image.

            .. warning:: Avoid quotes (", ') inside of the command, as those may lead to strange side effects.

        [additional_volumes]
            Additional volumes to mount into the container for this command.

            {key}
                host: str
                    Path on the host system to the volume. Avoid hardcoded absolute paths.
                container: str
                    Path inside the container (relative to src of Project or absolute).
                [mode]: str
                    Whether to mount the volume read-write ("rw", default) or read-only ("ro").
                [type]: str
                    Whether this volume is a "directory" (default) or a "file". Only checked if the file/dir does
                    not exist yet on the host system. Riptide will then create it with the appropriate type.
                [volume_name]: str
                    Name of a named volume for this additional volume. Used instead of "host" if present and
                    the dont_sync_named_volumes_with_host performance setting is enabled. Volumes with the same
                    volume_name have the same content, even across projects. As a constraint, the name of
                    two volumes should only be the same, if the host path specified is also the same, to ensure
                    the same behaviour regardless of if the performance setting is enabled.

        [environment]
            Additional environment variables

            {key}: str
                Key is the name of the variable, value is the value.

        [config_from_roles]: List[str]
            List of role names. All files defined under "config" for services matching the roles are mounted
            into the command container.

        [read_env_file]: bool
            If enabled, read the environment variables in the env-files defined in the project (``env_files``).
            Default: True

        [use_host_network]: bool
            If enabled, the container uses network mode `host`. Overrides network and port settings
            Default: False

        **Example Document:**

        .. code-block:: yaml

            command:
              image: riptidepy/php
              command: 'php index.php'
        """
        return Schema({
            Optional('$ref'): str,  # reference to other Service documents
            Optional('$name'): str,  # Added by system during processing parent app.

            'image': str,
            Optional('command'): str,
            Optional('additional_volumes'): {
                str: {
                    'host': str,
                    'container': str,
                    Optional('mode'): str,  # default: rw - can be rw/ro.
                    Optional('type'): Or('directory', 'file'),  # default: directory
                    Optional('volume_name'): str
                }
            },
            Optional('environment'): {str: str},
            Optional('config_from_roles'): [str],
            Optional('read_env_file'): bool,
            Optional('use_host_network'): bool,
        })

    @classmethod
    def schema_in_service(cls):
        """
        Command is run in a running service container.

        If the service container is not running, a new container is started based on the
        definition of the service.

        [$name]: str
            Name as specified in the key of the parent app.

            Added by system. DO NOT specify this yourself in the YAML files.

        in_service_with_role: str
            Runs the command in the first service which has this role.

            May lead to unexpected results, if multiple services match the role.

        command: str
            Command to run inside of the container.

            .. warning:: Avoid quotes (", ') inside of the command, as those may lead to strange side effects.

        [environment]
            Additional environment variables. The container also has access
            to the environment of the service.
            Variables in the current user's env will override those values and
            variables defined here, will override all other.

            {key}: str
                Key is the name of the variable, value is the value.

        [read_env_file]: bool
            If enabled, read the environment variables in the env-files defined in the project (``env_files``).
            Default: True

        [use_host_network]: bool
            If enabled, the container uses network mode `host`. Overrides network and port settings
            Default: False

        **Example Document:**

        .. code-block:: yaml

            command:
              in_service_with_role: php
              command: 'php index.php'
        """
        return Schema({
            Optional('$ref'): str,  # reference to other Service documents
            Optional('$name'): str,  # Added by system during processing parent app.

            KEY_IDENTIFIER_IN_SERVICE_COMMAND: str,
            'command': str,
            Optional('environment'): {str: str},
            Optional('read_env_file'): bool,
            Optional('use_host_network'): bool,
        })

    @classmethod
    def schema_alias(cls):
        """
        Aliases another command.

        [$name]: str
            Name as specified in the key of the parent app.

            Added by system. DO NOT specify this yourself in the YAML files.

        aliases: str
            Name of the command that is aliased by this command.
        """
        return Schema({
            Optional('$ref'): str,  # reference to other Service documents
            Optional('$name'): str,  # Added by system during processing parent app.

            'aliases': str
        })

    def _initialize_data_after_variables(self, data: dict) -> dict:
        """ Normalize all host-paths to only use the system-type directory separator """
        if "additional_volumes" in data:
            for obj in data["additional_volumes"].values():
                obj["host"] = cppath.normalize(obj["host"])

        if "read_env_file" not in self:
            data["read_env_file"] = True
        return data

    def get_project(self) -> 'Project':
        """
        Returns the project or raises an error if this is not assigned to a project

        :raises: IndexError: If not assigned to a project
        """
        try:
            return self.parent_doc.parent_doc
        except Exception as ex:
            raise IndexError("Expected command to have a project assigned") from ex

    def collect_volumes(self) -> OrderedDict:
        """
        Collect volume mappings that this command should be getting when running.

        Only applicable to commands matching the "normal" schema.

        Volumes are built from following sources:

        * Source code is mounted as volume if role "src" is set
        * SSH_AUTH_SOCKET path is added as a volume
        * additional_volumes are added.
        * All config files from all services matching the roles in 'config_from_roles' are added. No service
          is processed twice. Order is arbitrary, with the exception that roles are processed in the order they are
          defined in.

        :return: dict. Return format is the docker container API volumes dict format.
                       See: https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run
                       The volume definitions may contain an additional key 'name', which should be used by the engine,
                       instead of the host path if the dont_sync_named_volumes_with_host performance option is enabled.
        """
        project = self.get_project()
        volumes = OrderedDict({})

        # source code
        volumes[project.src_folder()] = {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'}

        # If SSH_AUTH_SOCK is set, provide the ssh auth socket as a volume
        if 'SSH_AUTH_SOCK' in os.environ:
            volumes[os.environ['SSH_AUTH_SOCK']] = {'bind': os.environ['SSH_AUTH_SOCK'], 'mode': 'rw'}

        # additional_volumes
        if "additional_volumes" in self:
            # Shared with services logic
            volumes.update(process_additional_volumes(list(self['additional_volumes'].values()), project.folder()))

        # config_from_role
        if "config_from_roles" in self:
            services_already_checked = []
            for role in self["config_from_roles"]:
                for service in self.parent().get_services_by_role(role):
                    if "config" in service and service not in services_already_checked:
                        services_already_checked.append(service)
                        for config_name, config in service["config"].items():
                            force_recreate = False
                            if "force_recreate" in service["config"][config_name] and service["config"][config_name]["force_recreate"]:
                                force_recreate = True
                            bind_path = str(PurePosixPath('/src/').joinpath(PurePosixPath(config["to"])))
                            process_config(volumes, config_name, config, service, bind_path, regenerate=force_recreate)

        return volumes

    def resolve_alias(self) -> 'Command':
        """ If this is not an alias, returns self. Otherwise returns command that is aliased by this (recursively). """
        if "aliases" in self:
            return self.parent()["commands"][self["aliases"]].resolve_alias()
        return self

    def collect_environment(self) -> dict:
        """
        Collect environment variables.

        The passed environment is simple all of the riptide's process environment,
        minus some important meta-variables such as USERNAME and PATH.

        Also collects all environment variables defined in command
        and sets LINES and COLUMNS based on terminal size.

        Additionally, all configurations in the ``.env`` file in the project folder are also
        passed to the container (if ``read_env_file``) is True).

        Environment priority:
        - Current shell environment variables.
        - Environment variables defined in the ``environment`` of the command.
        - Environment variables of the ``.env`` file.
        - LINES and COLUMNS from current terminal size.

        :return: dict. Returned format is ``{key1: value1, key2: value2}``.
        """
        env = os.environ.copy()
        keys_to_remove = {"PATH", "PS1", "USERNAME", "PWD", "SHELL", "HOME", "TMPDIR"}.intersection(set(env.keys()))
        for key in keys_to_remove:
            del env[key]

        if "environment" in self:
            for key, value in self['environment'].items():
                env[key] = value

        if "read_env_file" not in self or self["read_env_file"]:
            for env_file_path in self.get_project()['env_files']:
                env.update(dotenv_values(os.path.join(self.get_project().folder(), env_file_path)))

        try:
            cols, lines = os.get_terminal_size()
            env['COLUMNS'] = str(cols)
            env['LINES'] = str(lines)
        except OSError:
            pass

        return env

    def get_service(self, app: 'App') -> Union[str, None]:
        """
        Only applicable to "in service" commands.

        Returns the name of the service in app.

        Raises ValueError if the service does not exist in app or if not applicable.

        :param app: The app to search in
        :return: Name of the service (key) in app.
        """
        if KEY_IDENTIFIER_IN_SERVICE_COMMAND not in self.doc:
            raise TypeError('get_service can only be used on "in service" commands.')

        if 'services' not in app:
            raise ValueError(
                f"Command {(self['$name'] if '$name' in self else '???')} can not run in service with role "
                f"{self.doc[KEY_IDENTIFIER_IN_SERVICE_COMMAND]}: "
                f"The app has no services.")

        for service_name, service in app['services'].items():
            if 'roles' in service and self.doc[KEY_IDENTIFIER_IN_SERVICE_COMMAND] in service['roles']:
                return service_name

        raise ValueError(f"Command {(self['$name'] if '$name' in self else '???')} can not run in service with role "
                         f"{self.doc[KEY_IDENTIFIER_IN_SERVICE_COMMAND]}: "
                         f"No service with this role found in the app.")

    def error_str(self) -> str:
        return f"{self.__class__.__name__}<{(self.internal_get('$name') if self.internal_contains('$name') else '???')}>"

    @variable_helper
    def parent(self) -> 'App':
        """
        Returns the app that this command belongs to.

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
        Returns the (host) path to a command-unique directory for storing container data.

        Example usage::

            additional_volumes:
                command_cache:
                    host: '{{ volume_path() }}/command_cache'
                    container: '/foo/bar/cache'

        Example result::

            additional_volumes:
                command_cache:
                    host: '/home/peter/my_projects/project1/_riptide/cmd_data/command_name/command_cache'
                    container: '/foo/bar/cache'
        """
        path = os.path.join(get_project_meta_folder(self.get_project().folder()), 'cmd_data', self.internal_get("$name"))
        os.makedirs(path, exist_ok=True)
        return path
