import os

from typing import List

from schema import Schema, Optional

from configcrunch import YamlConfigDocument, DocReference, ConfigcrunchError
from configcrunch import load_subdocument
from riptide.config.document.app import App

HEADER = 'project'


class Project(YamlConfigDocument):

    @classmethod
    def header(cls) -> str:
        return HEADER

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
            if not isinstance(self["app"].doc, dict):
                raise ConfigcrunchError("Error loading App for Project: "
                                        "The app needs to be an object in the source document.")
        return self

    def folder(self):
        """Returns the project folder if $path if set or None otherwise"""
        if "$path" in self:
            return os.path.dirname(self["$path"])
        return None

    def src_folder(self):
        """Returns the absolute path to the folder specified by self['src']"""
        if "$path" not in self:
            return None
        return os.path.join(self.folder(), self["src"])
