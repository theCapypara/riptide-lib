from schema import Optional, Schema
from typing import List, Union

from configcrunch import YamlConfigDocument, DocReference, ConfigcrunchError
from configcrunch import load_subdocument
from configcrunch.abstract import variable_helper
from riptide.config.document.command import Command
from riptide.config.document.service import Service


HEADER = 'app'


class App(YamlConfigDocument):
    """
    An application.

    Consists of (multiple) :class:`riptide.config.document.service.Service`
    and (multiple) :class:`riptide.config.document.command.Command`
    and is usually included in a :class:`riptide.config.document.project.Project`.

    Example::

        app:
          name: example
          services:
            example:
              ...
          commands:
            example:
              ...
    """
    @classmethod
    def header(cls) -> str:
        return HEADER

    def schema(self) -> Schema:
        return Schema(
            {
                Optional('$ref'): str,  # reference to other App documents
                'name': str,
                Optional('notices'): {
                    Optional('usage'): str,
                    Optional('installation'): str
                },
                Optional('import'): {
                    str: {
                        'target': str,
                        'name': str
                    }
                },
                Optional('services'): {
                    str: DocReference(Service)
                },
                Optional('commands'): {
                    str: DocReference(Command)
                }
            }
        )

    def resolve_and_merge_references(self, lookup_paths: List[str]):
        super().resolve_and_merge_references(lookup_paths)
        if "services" in self:
            for key, servicedoc in self["services"].items():
                self["services"][key] = load_subdocument(servicedoc, self, Service, lookup_paths)
                if not isinstance(self["services"][key].doc, dict):
                    raise ConfigcrunchError("Error loading Service for App: "
                                            "The service with the name %s needs to be an object in the source document." % key)
                self["services"][key]["$name"] = key

        if "commands" in self:
            for key, commanddoc in self["commands"].items():
                self["commands"][key] = load_subdocument(commanddoc, self, Command, lookup_paths)
                if not isinstance(self["commands"][key].doc, dict):
                    raise ConfigcrunchError("Error loading Command for App: "
                                            "The command with the name %s needs to be an object in the source document." % key)
                self["commands"][key]["$name"] = key

        return self

    @variable_helper
    def get_service_by_role(self, role_name: str) -> Union[Service, None]:
        """
        Returns any service with the given role name (first found in an unordered dict).
        """
        for service in self["services"].values():
            if "roles" in service and role_name in service["roles"]:
                return service
