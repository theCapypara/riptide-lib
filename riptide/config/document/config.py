import platform
from typing import List, TYPE_CHECKING

import yaml
from schema import Schema, Optional, Or

from configcrunch import YamlConfigDocument, DocReference, variable_helper
from riptide.config.document.project import Project
from riptide.config.files import riptide_main_config_file, riptide_config_dir
from riptide.plugin.loader import load_plugins

if TYPE_CHECKING:
    from riptide.engine.abstract import AbstractEngine

HEADER = 'riptide'


class Config(YamlConfigDocument):
    """
    System configuration. Contains basic settings
    for Riptide.

    After loading a :class:`riptide.config.document.project.Project`,
    the project must be inserted into the ``project`` key.

    """
    @classmethod
    def header(cls) -> str:
        return HEADER

    @classmethod
    def schema(cls) -> Schema:
        """
        proxy
            url: str
                Base-URL for the proxy server. The name of projects and/or services will be appended to it.

                For example `projectname.riptide.local` would route to the
                project `projectname` if `riptide.local` is specified.
            ports
                http: int
                    HTTP port that the proxy server should listen on
                https: Or[int,bool]
                    HTTPS port that the proxy server should listen on, or false to disable HTTPS

            autostart: bool
                Whether or not the proxy server should auto-start all services for a project
                if a user enters the URL for a service.

            [autostart_restrict]: List[str]
                If set, only the IPv4 ip addresses specified by the netmasks in this list are allowed
                to trigger the auto-start process via the proxy server. For other clients, projects
                are not automatically started. Useful if you share a network with co-workers and don't
                want them to start your projects.

            [compression]: bool
                If true, the proxy server doesn't decompress any data, and instead passes the compressed
                data of the backend server (if compressed). Experimental.

        engine: str
            Engine to use, the Python package for the engine must be installed.

        repos: List[str]
            List of URLs to Git repositories containing
            `Riptide Repositories </config_docs/using_repo/how_repositories.html>`_.

        update_hosts_file: bool
            Whether or not Riptide should automatically update the
            `system's host file </user_docs/3_installing.html#resolving-hostnames-permissions-for-the-etc-hosts-file>`_.

        [project]: :class:`~riptide.config.document.project.Project`
            If a project is loaded, Riptide inserts the project here. Do not manually insert a project
            into the actual system configuration file.

        performance
            Various performance optimizations that, when enabled, increase the performance
            of containers, but might have some other drawbacks.

            Values can be true/false/auto.
            "auto" enables an optimization, if beneficial on your platform.

            dont_sync_named_volumes_with_host: Or['auto',bool]
                If enabled, volumes, that have a volume_name set, are not mounted to the host system
                and are instead created as volumes with the volume_name. Otherwise they
                are created as host path volumes only. Enabling this increases
                performance on some platforms.

                Please note, that Riptide does not delete named volume data for old projects.
                Please consult the documentation of the engine, on how to do that.

                "auto" enables this feature on Mac and Windows, when using the Docker
                container backend.

                Switching this setting on or off breaks existing volumes. They need to be
                migrated manually.

            dont_sync_unimportant_src: Or['auto', bool]
                Normally all Commands and Services get access to the entire source
                directory of a project as volume. If this setting is enabled,
                ``unimportant_paths`` that are defined in the App are not updated
                on the host system when changed by the volume. This means changes
                to these files are not available, but file access speeds may be
                drastically increased on some platforms.

                "auto" enables this feature on Mac and Windows, when using the Docker
                container backend.

                This feature can be safely switched on or off. Projects need to be
                restarted for this to take effect.

        **Example Document:**

        .. code-block:: yaml

            riptide:
              proxy:
                url: riptide.local
                ports:
                  http: 80
                  https: 443
                autostart: true
                autostart_restrict:
                  - 127.0.0.1/32
              engine: docker
              repos:
                - https://github.com/theCapypara/riptide-repo.git
              update_hosts_file: true
              performance:
                dont_sync_named_volumes_with_host: auto
                dont_sync_unimportant_src: auto

        """
        return Schema(
            {
                'proxy': {
                    'url': str,
                    'ports': {
                        'http': int,
                        'https': Or(int, False)  # False disables HTTPS
                    },
                    'autostart': bool,
                    Optional('autostart_restrict'): [str],
                    Optional('compression'): bool,
                    Optional('autoexit'): int  # TODO: Not used, deprecated.
                },
                'update_hosts_file': bool,
                'engine': str,
                'repos': [str],
                Optional('project'): DocReference(Project),  # Added and overwritten by system
                # Performance entries should be added by the system to the YAML file before validation if missing:
                'performance': {
                    'dont_sync_named_volumes_with_host': Or(bool, 'auto'),
                    'dont_sync_unimportant_src': Or(bool, 'auto')
                }
            }
        )

    @classmethod
    def subdocuments(cls):
        # Can not contain references to other documents other than
        # the "project" reference which is added by the system.
        return []

    def error_str(self) -> str:
        return "System Configuration"

    @variable_helper
    def get_config_dir(self):
        """
        Returns the path to the Riptide system configuration directory

        Example usage::

            something: '{{ get_config_dir() }}'

        Example result::

            something: '/home/thomas/.config/riptide'

        """
        return riptide_config_dir()

    @variable_helper
    def get_plugin_flag(self, inp: str) -> any:
        """
        Returns the value (usually true/false, but can also be other data) of a flag set by a Riptide plugin.

        If the flag or plugin is not found, false is returned.

        :param inp: plugin-name.flag-name
        """
        plugin_name_and_flag_name = inp.split('.', 1)
        all_plugins = load_plugins()
        if plugin_name_and_flag_name[0] in all_plugins:
            return load_plugins()[plugin_name_and_flag_name[0]].get_flag_value(self, plugin_name_and_flag_name[1])
        return False

    def upgrade(self):
        """Update the system configuration file after Riptide version upgrades. To be run before validation."""
        changed = False
        with self.internal_access():
            if "performance" not in self.doc:
                self.doc["performance"] = {}
                changed = True
            if "dont_sync_named_volumes_with_host" not in self.doc["performance"]:
                self.doc["performance"]["dont_sync_named_volumes_with_host"] = "auto"
                changed = True
            if "dont_sync_unimportant_src" not in self.doc["performance"]:
                self.doc["performance"]["dont_sync_unimportant_src"] = "auto"
                changed = True

            if changed:
                with open(riptide_main_config_file(), "w") as f:
                    f.write(yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False))

    def load_performance_options(self, engine: 'AbstractEngine'):
        """Initializes performance options set to 'auto' based on the engine used."""
        for key, val in self.doc["performance"].items():
            if val == 'auto':
                self.doc["performance"][key] = engine.performance_value_for_auto(key, platform.system().lower())
