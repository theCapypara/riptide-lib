from typing import List

from schema import Schema, Optional, Or

from configcrunch import YamlConfigDocument, DocReference
from riptide.config.document.project import Project

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

    def schema(self) -> Schema:
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

        **Example Document:**

        .. code-block:: yaml

            riptide:
              proxy:
                url: riptide.local
                ports:
                  http: 80
                  https: 443
                autostart: true
              engine: docker
              repos:
                - https://github.com/Parakoopa/riptide-repo.git
              update_hosts_file: true

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
                    Optional('autoexit'): int  # TODO: Not used, deprecated.
                },
                'update_hosts_file': bool,
                'engine': str,
                'repos': [str],
                Optional('project'): DocReference(Project)  # Added and overwritten by system
            }
        )

    def resolve_and_merge_references(self, lookup_paths: List[str]) -> 'YamlConfigDocument':
        # Can not contain references to other documents other than
        # the "project" reference which is added by the system.
        return self

    def error_str(self) -> str:
        return "System Configuration"
