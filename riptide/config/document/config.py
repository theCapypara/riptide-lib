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

    Example document::

        riptide:
          proxy:
            url: riptide.local
            ports:
              http: 80
              https: 443
            autostart: true
            autoexit: 15

          repos: []

          engine: docker

    """
    @classmethod
    def header(cls) -> str:
        return HEADER

    def schema(self) -> Schema:
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
