from schema import Optional, Schema
from typing import List, Union, TYPE_CHECKING

from configcrunch import YamlConfigDocument, DocReference, ConfigcrunchError
from configcrunch import load_subdocument
from configcrunch.abstract import variable_helper
from riptide.config.document.command import Command
from riptide.config.document.service import Service

if TYPE_CHECKING:
    from riptide.config.document.project import Project

HEADER = 'app'


class App(YamlConfigDocument):
    """
    An application.

    Consists of (multiple) :class:`riptide.config.document.service.Service`
    and (multiple) :class:`riptide.config.document.command.Command`
    and is usually included in a :class:`riptide.config.document.project.Project`.
    """
    @classmethod
    def header(cls) -> str:
        return HEADER

    def schema(self) -> Schema:
        """
        name: str
            Name describing this app.

        [notices]
            [usage]: str
                Text that will be shown when the interactive `setup wizard </user_docs/4_project.html>`_ ist started.

                This text should describe additional steps needed to finish the setup of the app and general
                usage notes.

            [installation]: str
                Text that will be shown, when the user selects a new installation (from scratch) for this app.

                This text should explain how to execute the first-time-setup of this app when using Riptide.

        [import]
            {key}
                Files and directories to import during the interactive setup wizard.

                target: str
                    Target path that the file or directory should be imported to,
                    relative to the directory of the riptide.yml

                name: str
                    Human-readable name of this import file. This is displayed during the interactive setup and should
                    explain what kind of file or directory is imported.

        [services]
            {key}: :class:`~riptide.config.document.service.Service`
                Services for this app.

        [commands]
            {key}: :class:`~riptide.config.document.command.Command`
                Commands for this app.


        **Example Document:**

        .. code-block:: yaml

            app:
              name: example
              notices:
                usage: Hello World!
              import:
                example:
                  target: path/inside/project
                  name: Example Files
              services:
                example:
                  $ref: /service/example
              commands:
                example:
                  $ref: /command/example
        """
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

    def error_str(self) -> str:
        return "%s<%s>" % (self.__class__.__name__, self["name"] if "name" in self else "???")

    @variable_helper
    def parent(self) -> 'Project':
        """
        Returns the project that this app belongs to.

        Example usage::

            something: '{{ parent().src }}'

        Example result::

            something: '.'
        """
        # noinspection PyTypeChecker
        return super().parent()

    @variable_helper
    def get_service_by_role(self, role_name: str) -> Union[Service, None]:
        """
        Returns any service with the given role name (first found) or None.

        Example usage::

            something: '{{ get_service_by_role("main")["$name"] }}'

        Example result::

            something: 'service1'

        :param role_name: Role to search for
        """
        for service in self["services"].values():
            if "roles" in service and role_name in service["roles"]:
                return service
