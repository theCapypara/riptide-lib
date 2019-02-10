from schema import Optional, Schema
from typing import List

from configcrunch import YamlConfigDocument, DocReference
from configcrunch import load_subdocument
from configcrunch.abstract import variable_helper
from riptide.config.document.command import Command
from riptide.config.document.service import Service


class App(YamlConfigDocument):

    @classmethod
    def header(cls) -> str:
        return "app"

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
                'services': {
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
                self["services"][key]["$name"] = key

        if "commands" in self:
            for key, commanddoc in self["commands"].items():
                self["commands"][key] = load_subdocument(commanddoc, self, Command, lookup_paths)
                self["commands"][key]["$name"] = key

        return self

    @variable_helper
    def get_service_by_role(self, role_name):
        """ TODO """
        for service in self["services"].values():
            if "roles" in service and role_name in service["roles"]:
                return service
