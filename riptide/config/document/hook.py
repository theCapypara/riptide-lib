from __future__ import annotations

import shlex
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Mapping, Sequence

from configcrunch import DocReference, YamlConfigDocument
from riptide.config.document import DocumentClass, RiptideDocument
from riptide.config.document.command import Command
from riptide.config.files import CONTAINER_SRC_PATH
from riptide.hook.event import AnyHookEvent, HookEvent
from schema import Optional, Or, Schema

if TYPE_CHECKING:
    from riptide.config.document.app import App
    from riptide.config.document.config import Config

HEADER = "hook"


class Hook(RiptideDocument):
    """
    A hook. Hooks are executed when certain events occur and behave the same as
    :class:`riptide.config.document.command.Command`.

    Events that trigger hooks are defined in :class:`riptide.hook.HookEvent`. Additionally, user-defined
    custom events can be defined by prefixing an event name with ``custom-``.

    Hooks can either run a command from a normal Command definition (including referencing commands from
    any configured repository) or execute a command defined in the Project's App.

    Hooks are usually defined as part of an :class:`riptide.config.document.app.App` but can also be globally
    defined. Globally defined hooks are only triggered if a project is loaded, Riptide never executes hooks
    if no project is loaded.

    Hooks can be managed and executed using the ``hook`` command group of ``riptide-cli``.

    If multiple hooks are defined for one event, they are executed in an arbitrary order. This means that hooks
    may not rely on other hooks being executed.

    For all command hooks run, the entire current project is mounted under ``/project`` and the hooks
    have access to all environment variables of the shell (normal command rules apply).
    ``/src`` is still mounted as normal, the working directory is also defined relative to ``/src``.
    """

    identity = DocumentClass.Hook

    parent_doc: App | Config | None
    events: set[AnyHookEvent]

    @classmethod
    def header(cls) -> str:
        return HEADER

    @classmethod
    def schema(cls) -> Schema:
        """
        [$name]: str
            Name as specified in the key of the parent app.

            Added by system. DO NOT specify this yourself in the YAML files.

        events: List[str]
            List of events that trigger this hook.

        [continue_on_error]: bool
            Defaults to False. If True the hook will interrupt (in most cases, some Git Hooks always ignore failure)
            whatever process caused it to trigger and fail with an error. Any further hook is not executed.
            This will cause ``riptide hook-trigger`` to exit with a non-zero exit code. If this is False,
            any error is ignored.

        [pass_event_arguments]: bool
            Defaults to true. If True, arguments related to the event are passed to the command, if False,
            they are not. If and what arguments would be passed depends on the event, see documentation.

        [working_directory]: str
            Working directory for the hook command, relative to the ``src`` specified in the project

            If not given, the command is executed in the ``src`` directory.

        command:
            This can take two forms:

                1. Command definition

                    run: Command
                        A :class:`~riptide.config.document.service.Command` object.

                    Riptide will trigger this command like Riptide executes any Command under any other circumstance.

                2. Command from App

                    from_app: str
                        Key of a command defined in the app, must exist.

                    [args]: str
                        Additional arguments to pass to the command. These are passed before event arguments
                        (see ``pass_event_arguments``).

                    When using the "command from app" form, Riptide will execute the command defined in the app like normal
                    and optionally pass the list of arguments to it. They will be passed as-is as if they were typed on the
                    command line by bash, and parsed as such.

                    This form is not allowed for hooks which are globally defined. Trying to use
                    such a hook in the :class:`riptide.config.document.config.Config` will result in Riptide refusing
                    to operate.


        **Example Document:**

        .. code-block:: yaml

            hook:
              events:
                - git-pre-commit
                - post-start
                - custom-post-magic
              continue_on_error: true
              working_directory: www
              command:
                run:
                  $ref: /command/my_check
        """
        return Schema(
            {
                Optional("$ref"): str,  # reference to other Hook documents
                Optional("$name"): str,  # Added by system during processing parent app.
                "events": [str],  # Must be valid `AnyHookEvent`.
                Optional("continue_on_error"): bool,
                Optional("pass_event_arguments"): bool,
                Optional("working_directory"): str,
                "command": Or(Schema({"run": DocReference(Command)}), Schema({"from_app": str, Optional("args"): str})),
            }
        )

    @classmethod
    def subdocuments(cls) -> list[tuple[str, type[YamlConfigDocument]]]:
        return [
            ("command/run", Command),
        ]

    def _initialize_data_after_merge(self, data):
        self.events = set()
        return data

    def validate(self) -> bool:
        if not super().validate():
            return False

        self.validate_and_assign_events()
        return True

    def continue_on_error(self) -> bool:
        if self.internal_contains("continue_on_error"):
            return self.internal_get("continue_on_error")
        return False

    def pass_event_arguments(self) -> bool:
        if self.internal_contains("pass_event_arguments"):
            return self.internal_get("pass_event_arguments")
        return True

    def get_working_directory(self) -> str | None:
        """
        Returns the path to the working directory **inside** the container.
        """
        workdir = CONTAINER_SRC_PATH
        if self.internal_contains("working_directory"):
            if PurePosixPath(self.internal_get("working_directory")).is_absolute():
                raise ValueError("Hook working directories can not be absolute.")
            elif workdir is not None:
                return str(PurePosixPath(workdir).joinpath(self.internal_get("working_directory")))
        return workdir

    def validate_and_assign_events(self):
        for event in self.internal_get("events"):
            event_cast = HookEvent.validate(event)
            if not event_cast:
                raise KeyError(f"{event} is not a valid hook event")
            self.events.add(event_cast)

    def matches_event(self, event: AnyHookEvent) -> bool:
        return event in self.events

    def command(self) -> Command:
        cmd_info = self.internal_get("command")
        if "run" in cmd_info:
            return cmd_info["run"]

        parent = self.parent_doc
        if parent is not None and parent.identity == DocumentClass.App:
            app_commands: Mapping[str, Command] = parent["commands"]
            if cmd_info["from_app"] not in app_commands:
                raise ValueError(
                    f"The command `{cmd_info['from_app']}` does not exist in the app but was requested in a hook."
                )
            return app_commands[cmd_info["from_app"]]
        else:
            raise ValueError(
                "`from_app` can not be used with hooks that are defined globally in the user configuration"
            )

    def args(self, event_args: Sequence[str]) -> list[str]:
        """
        Returns the arguments that should be passed to the command (in addition to arguments defined in the
        command object returned by ``command``. The arguments ``event_args`` passed into this function are added, if
        ``pass_event_arguments`` is True.
        """

        cmd_info = self.internal_get("command")
        if "args" in cmd_info:
            args = shlex.split(cmd_info["args"])
        else:
            args = []

        if self.pass_event_arguments():
            return [*args, *event_args]
        return args
