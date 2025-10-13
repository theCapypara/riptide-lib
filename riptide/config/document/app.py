from __future__ import annotations

from typing import TYPE_CHECKING

from configcrunch import DocReference, YamlConfigDocument, variable_helper
from riptide.config.document import DocumentClass, RiptideDocument
from riptide.config.document.command import Command
from riptide.config.document.hook import Hook
from riptide.config.document.service import Service
from schema import Optional, Schema

if TYPE_CHECKING:
    from riptide.config.document.project import Project

HEADER = "app"


class App(RiptideDocument):
    """
    An application.

    Consists of (multiple) :class:`riptide.config.document.service.Service`
    and (multiple) :class:`riptide.config.document.command.Command`
    and is usually included in a :class:`riptide.config.document.project.Project`.
    """

    identity = DocumentClass.App

    parent_doc: Project | None

    @classmethod
    def header(cls) -> str:
        return HEADER

    @classmethod
    def schema(cls) -> Schema:
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

        [hooks]
            {key}: :class:`~riptide.config.document.hook.Hook`
                Hooks for this app.

        [unimportant_paths]: List[str]
            Normally all files inside containers are shared with the host (for commands and services with role 'src').
            This list specifies files that don't need to be synced with the host. This means, that these files
            will only be uploaded to the container on start and changes will not be visible on the host. Changes that
            are made on the host file system may also not be visible inside the container. This increases performance
            on non-native platforms (Mac and Windows).

            This feature is only enabled if the system configuration performance setting ``dont_sync_unimportant_src``
            is enabled. If the feature is disabled, all files are shared with the host. See the documentation for that
            setting for more information.

            All paths are relative to the src of the project. Only directories are supported.


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
                Optional("$ref"): str,  # reference to other App documents
                "name": str,
                Optional("notices"): {Optional("usage"): str, Optional("installation"): str},
                Optional("import"): {str: {"target": str, "name": str}},
                Optional("services"): {Optional(str): DocReference(Service)},
                Optional("commands"): {Optional(str): DocReference(Command)},
                Optional("hooks"): {Optional(str): DocReference(Hook)},
                Optional("unimportant_paths"): [str],
            }
        )

    @classmethod
    def subdocuments(cls) -> list[tuple[str, type[YamlConfigDocument]]]:
        return [
            ("services[]", Service),
            ("commands[]", Command),
            ("hooks[]", Hook),
        ]

    def validate(self):
        """
        Initialise the optional services, command and hook dicts.
        Has to be done after validate because of some issues with Schema validation error handling :(
        """
        ret_val = super().validate()
        if ret_val:
            if not self.internal_contains("services"):
                self.internal_set("services", {})
            if not self.internal_contains("commands"):
                self.internal_set("commands", {})
            if not self.internal_contains("hooks"):
                self.internal_set("hooks", {})
        return ret_val

    def error_str(self) -> str:
        return f"{self.__class__.__name__}<{(self.internal_get('name') if self.internal_contains('name') else '???')}>"

    @variable_helper
    def parent(self) -> Project:
        """
        Returns the project that this app belongs to.

        Example usage::

            something: '{{ parent().src }}'

        Example result::

            something: '.'
        """
        parent = super().parent()
        if TYPE_CHECKING:
            assert isinstance(parent, Project)
        return parent

    @variable_helper
    def get_service_by_role(self, role_name: str) -> Service | None:
        """
        Returns any service with the given role name (first found) or None.

        Example usage::

            something: '{{ get_service_by_role("main")["$name"] }}'

        Example result::

            something: 'service1'

        :param role_name: Role to search for
        """
        for service in self.internal_get("services").values():
            if service.internal_contains("roles") and role_name in service.internal_get("roles"):
                return service
        raise ValueError(f"No service with role {role_name} found in the app.")

    @variable_helper
    def get_services_by_role(self, role_name: str) -> list[Service]:
        """
        Returns all services with the given role name.

        :param role_name: Role to search for
        """
        services = []
        for service in self.internal_get("services").values():
            if service.internal_contains("roles") and role_name in service.internal_get("roles"):
                services.append(service)
        return services
