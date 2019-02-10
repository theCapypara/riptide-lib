import os

from typing import List

from schema import Schema, Optional

from configcrunch import YamlConfigDocument, DocReference
from configcrunch import load_subdocument
from riptide.config.document.app import App


class Project(YamlConfigDocument):

    @classmethod
    def header(cls) -> str:
        return "project"

    def schema(self) -> Schema:
        return Schema(
            {
                Optional('$ref'): str,  # reference to other Project documents
                Optional('$path'): str,  # Path to the project file, added by system after loading.
                'name': str,
                'src': str,
                'app': DocReference(App)
            }
        )

    def resolve_and_merge_references(self, lookup_paths: List[str]):
        super().resolve_and_merge_references(lookup_paths)
        if "app" in self:
            self["app"] = load_subdocument(self["app"], self, App, lookup_paths)
        return self

    def folder(self):
        """Returns the project folder if $path if set or None otherwise"""
        if "$path" in self:
            return os.path.dirname(self["$path"])
        return None

    def src_folder(self):
        """Returns the absolute path to the folder specified by self['src']"""
        return os.path.join(self.folder(), self["src"])
