from collections import OrderedDict

import os
from pathlib import PurePosixPath

from schema import Schema, Optional, Or
from typing import TYPE_CHECKING

from configcrunch import YamlConfigDocument
from configcrunch.abstract import variable_helper
from riptide.config.files import get_project_meta_folder, CONTAINER_SRC_PATH, CONTAINER_HOME_PATH
from riptide.lib.cross_platform import cppath

if TYPE_CHECKING:
    from riptide.config.document.project import Project


HEADER = 'command'


class Command(YamlConfigDocument):
    """
    A command document. Specifies a CLI command to be executable by the user.

    Placed inside an :class:`riptide.config.document.app.App`.

    Example::

        command:
          image: xyztest/helloworld

    """
    @classmethod
    def header(cls) -> str:
        return HEADER

    def schema(self) -> Schema:
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
        * additional_volumes are added.

        :return: dict. Return format is the docker container API volumes dict format.
                       See: https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run
        """
        project = self.get_project()
        volumes = OrderedDict({})

        # source code
        volumes[project.src_folder()] = {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'}

        # additional_volumes
        # todo: merge with services logic
        if "additional_volumes" in self:
            for vol in self["additional_volumes"].values():
                # ~ paths
                if vol["host"][0] == "~":
                    vol["host"] = os.path.expanduser("~") + vol["host"][1:]
                # Relative paths
                if not os.path.isabs(vol["host"]):
                    vol["host"] = os.path.join(project.folder(), vol["host"])

                # relative container paths
                if not PurePosixPath(vol["container"]).is_absolute():
                    vol["container"] = str(PurePosixPath(CONTAINER_SRC_PATH).joinpath(vol["container"]))

                mode = vol["mode"] if "mode" in vol else "rw"
                volumes[vol["host"]] = {'bind': vol["container"], 'mode': mode}

        return volumes

    def resolve_alias(self) -> 'Command':
        """ If this is not an alias, returns self. Otherwise returns command that is aliased by this (recursively). """
        if "aliases" in self:
            return self.parent()["commands"][self["aliases"]].resolve_alias()
        return self

    def collect_environment(self) -> dict:
        """
        Collect environment variables from the "environment" entry in the service
        configuration.

        TODO: This propably is really not the best idea

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

    @variable_helper
    def volume_path(self):
        """Returns the path to a command-unique directory for storing container data."""
        path = os.path.join(get_project_meta_folder(self.get_project().folder()), 'cmd_data', self["$name"])
        os.makedirs(path, exist_ok=True)
        return path

    @variable_helper
    def home_path(self):
        """Returns the path to the home directory inside the container."""
        return CONTAINER_HOME_PATH
