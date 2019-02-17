from typing import List

from schema import Schema, Optional

from configcrunch import YamlConfigDocument, DocReference
from riptide.config.document.project import Project

HEADER = 'riptide'


class Config(YamlConfigDocument):

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
                        'https': int
                    },
                    'autostart': bool,
                    'autoexit': int
                },
                'engine': str,
                'repos': [str],
                Optional('project'): DocReference(Project)  # Added and overwritten by system
            }
        )

    def resolve_and_merge_references(self, lookup_paths: List[str]) -> 'YamlConfigDocument':
        # Can not contain references to other documents other than the "project" reference which is added by the system.
        return self
