from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Sequence

from riptide.engine.abstract import AbstractEngine
from riptide.hook.event import AnyHookEvent

if TYPE_CHECKING:
    from riptide.config.document.config import Config


class AbstractPlugin(ABC):
    """
    A Riptide plugin extends the functionality of Riptide.

    For this it can:

    - Add new CLI commands to riptide-cli.
    - Set flags, which can be retrieved from the configuration using a variable helper
    - Directly read and modify all parts of the configuration entities loaded.
    - Communicate with the loaded engine.
    - Respond to events.
    """

    @abstractmethod
    def after_load_engine(self, engine: AbstractEngine):
        """After the engine was loaded. ``engine`` is the interface of the configured engine."""

    @abstractmethod
    def after_load_cli(self, main_cli_object):
        """
        Called after the last CLI of Riptide CLI has loaded. Can be used to add CLI commands using Click.
        The passed object is the main CLI command object.
        """

    @abstractmethod
    def after_reload_config(self, config: Config):
        """Called whenever a project is loaded or if the initial configuration is loaded without a project."""

    # noinspection PyMethodMayBeStatic
    def responds_to_event(self, event: AnyHookEvent) -> bool:
        """
        Returns whether this plugin responds to the given event.

        ``event_triggered`` will be called for these events if so.
        """
        return False

    # noinspection PyMethodMayBeStatic
    def event_triggered(self, config: Config, event: AnyHookEvent, arguments: Sequence[str]) -> int:
        """
        Called when an event is triggered, unless the user has disabled hooks for the given event.
        Only triggered if ``responds_to_event`` returns ``True`` for this event.

        The plugin may output to stdout or stderr to indicate what it is doing, if it is processing a hook.
        Please note that no visual indication of your event handler being run is printed by Riptide itself.
        If the task you are doing could take some time, you should print some status indication/feedback.

        The function must return an exit code. 0 means success, Riptide will continue. On a non-zero exit code,
        Riptide will abort the current process and exit with that error code. Note that for Git Hooks, git may
        ignore this exit code.
        """
        return 0

    @abstractmethod
    def get_flag_value(self, config: Config, flag_name: str) -> Any:
        """
        Return the value of a requested plugin flag. Return False if not defined.
        The current config is passed, to give a context about the calling project.
        Please note, that flag values are usually loaded before after_reload_config!
        """
