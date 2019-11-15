import os

from typing import List, TYPE_CHECKING

from schema import Schema, Optional

from configcrunch import YamlConfigDocument, DocReference, ConfigcrunchError, variable_helper, REMOVE
from configcrunch import load_subdocument
from riptide.config.document.app import App

HEADER = 'project'

if TYPE_CHECKING:
    from riptide.config.document.config import Config


class Project(YamlConfigDocument):
    """
    A project file. Usually placed as ``riptide.yml`` inside the project directory.
    Has an :class:`riptide.config.document.app.App` in it's ``app`` entry.

    """
    @classmethod
    def header(cls) -> str:
        return HEADER

    @classmethod
    def schema(cls) -> Schema:
        """
        name: str
            Unique name of the project.

        src: str
            Relative path of the source code directory (relative to riptide.yml).
            Services and Commands only get access to this directory.

        app: :class:`~riptide.config.document.app.App`
            App that this project uses.

        **Example Document:**

        .. code-block:: yaml

            project:
              name: test-project
              src: src
              app:
                $ref: apps/reference-to-app

        """
        return Schema(
            {
                Optional('$ref'): str,  # reference to other Project documents
                Optional('$path'): str,  # Path to the project file, added by system after loading.
                'name': str,
                'src': str,
                'app': DocReference(App)
            }
        )

    def _load_subdocuments(self, lookup_paths: List[str]):
        if "app" in self and self["app"] != REMOVE:
            self["app"] = load_subdocument(self["app"], self, App, lookup_paths)
            if not isinstance(self["app"].doc, dict):
                raise ConfigcrunchError("Error loading App for Project: "
                                        "The app needs to be an object in the source document.")
        return self

    def folder(self):
        """Returns the project folder if the special internal field "$path" if set or None otherwise"""
        if "$path" in self:
            return os.path.dirname(self["$path"])
        return None

    def src_folder(self):
        """Returns the absolute path to the folder specified by self['src']. Requires "$path" to be set."""
        if "$path" not in self:
            return None
        return os.path.join(self.folder(), self["src"])

    def error_str(self) -> str:
        return f"{self.__class__.__name__}<{(self['name'] if 'name' in self else '???')}>"

    @variable_helper
    def parent(self) -> 'Config':
        """
        Returns the system configuration document.

        Example usage::

            something: '{{ parent().proxy.url }}'

        Example result::

            something: 'riptide.local'

        """
        # noinspection PyTypeChecker
        return super().parent()
