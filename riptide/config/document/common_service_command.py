"""Common base class for simple static variable helpers for commands and services"""
import tempfile
from abc import ABC
from typing import TYPE_CHECKING

from configcrunch import variable_helper, YamlConfigDocument
from riptide.config.files import CONTAINER_HOME_PATH
from riptide.engine.abstract import RIPTIDE_HOST_HOSTNAME
from riptide.lib.cross_platform.cpuser import getuid, getgid

if TYPE_CHECKING:
    from riptide.config.document.config import Config


class ContainerDefinitionYamlConfigDocument(YamlConfigDocument, ABC):
    @classmethod
    def subdocuments(cls):
        return []

    @variable_helper
    def system_config(self) -> 'Config':
        """
        Returns the system configuration.

        Example usage::

            something: '{{ system_config().proxy.ports.http }}'

        Example result::

            something: '80'
        """
        # noinspection PyTypeChecker
        #              => App.  Project. Config
        return super().parent().parent().parent()

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
    def get_tempdir(self) -> str:
        """
        Returns the path to the system (host!) temporary directory where the user (should) have write access.

        Example usage::

            something: '{{ get_tempdir() }}'

        Example result::

            something: '/tmp'
        """
        return tempfile.gettempdir()
