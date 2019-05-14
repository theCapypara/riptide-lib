from collections import OrderedDict

import os
from pathlib import PurePosixPath

from schema import Schema, Optional, Or
from typing import TYPE_CHECKING

from configcrunch import YamlConfigDocument
from configcrunch.abstract import variable_helper
from riptide.config.files import get_project_meta_folder, CONTAINER_SRC_PATH, CONTAINER_HOME_PATH
from riptide.config.service.volumes import process_additional_volumes
from riptide.lib.cross_platform import cppath

if TYPE_CHECKING:
    from riptide.config.document.project import Project
    from riptide.config.document.app import App


HEADER = 'command'


class Command(YamlConfigDocument):
    """
    A command document. Specifies a CLI command to be executable by the user.

    Placed inside an :class:`riptide.config.document.app.App`.

    """
    @classmethod
    def header(cls) -> str:
        return HEADER

    def schema(self) -> Schema:
        """
        Can be either a normal command or an alias command.

        **Normal command**:

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

        [environment]
            Additional environment variables

            {key}: str
                Key is the name of the variable, value is the value.


        **Alias command**:

        [$name]: str
            Name as specified in the key of the parent app.

            Added by system. DO NOT specify this yourself in the YAML files.

        aliases: str
            Name of the command that is aliased by this command.

        **Example Document:**

        .. code-block:: yaml

            command:
              image: riptidepy/php
              command: 'php index.php'

        """
        return Schema(
            Or({
                Optional('$ref'): str,  # reference to other Service documents
                Optional('$name'): str,  # Added by system during processing parent app.

                'image': str,
                Optional('command'): str,
                Optional('additional_volumes'): {
                    str: {
                        'host': str,
                        'container': str,
                        Optional('mode'): str  # default: rw - can be rw/ro.
                    }
                },
                Optional('environment'): {str: str}
            }, {
                Optional('$ref'): str,  # reference to other Service documents
                Optional('$name'): str,  # Added by system during processing parent app.

                'aliases': str
            })
        )

    def _initialize_data_after_variables(self):
        """ Normalize all host-paths to only use the system-type directory separator """
        if "additional_volumes" in self:
            for obj in self.doc["additional_volumes"].values():
                obj["host"] = cppath.normalize(obj["host"])

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

        Volumes are built from following sources:

        * Source code is mounted as volume if role "src" is set
        * SSH_AUTH_SOCKET path is added as a volume
        * additional_volumes are added.

        :return: dict. Return format is the docker container API volumes dict format.
                       See: https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run
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

        Adds HOME to be /home_cmd.

        Also collects all environment variables defined in command
        and sets LINES and COLUMNS based on terminal size.

        :return: dict. Returned format is ``{key1: value1, key2: value2}``.
        """
        env = os.environ.copy()
        keys_to_remove = {"PATH", "PS1", "USERNAME", "PWD", "SHELL", "HOME", "TMPDIR"}.intersection(set(env.keys()))
        for key in keys_to_remove:
            del env[key]

        if "environment" in self:
            for key, value in self['environment'].items():
                env[key] = value

        try:
            cols, lines = os.get_terminal_size()
            env['COLUMNS'] = str(cols)
            env['LINES'] = str(lines)
        except OSError:
            pass

        return env

    def error_str(self) -> str:
        return "%s<%s>" % (self.__class__.__name__, self["$name"] if "$name" in self else "???")

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
        path = os.path.join(get_project_meta_folder(self.get_project().folder()), 'cmd_data', self["$name"])
        os.makedirs(path, exist_ok=True)
        return path

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
