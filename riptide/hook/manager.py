from __future__ import annotations

import itertools
import json
import os
import stat
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    Mapping,
    Protocol,
    Sequence,
    TypedDict,
    TypeVar,
)

from riptide.config.document.config import Config
from riptide.config.document.hook import Hook
from riptide.config.files import (
    get_project_hooks_config_file_path,
    riptide_hooks_config_file,
)
from riptide.hook.event import AnyHookEvent, HookEvent

GITHOOK_NEEDLE_RIPTIDE_HOOKS = "### RIPTIDE HOOK CONFIG BEGIN"

T = TypeVar("T")


class HookFlagConfiguration(Generic[T], TypedDict):
    """Value of a hook/event configuration"""

    effective: T  # Current effective configuration value
    default: T | None  # Configured global default value
    project: T | None  # Configured project value


class LoadedHookConfiguration(TypedDict):
    """Information about a loaded hook"""

    key: str
    hook: Hook
    defined_in: Literal["default"] | Literal["project"]


class ApplicableEventConfiguration(TypedDict):
    """Current applicable hook and event configuration, based on the result of all involved configuration files"""

    event: AnyHookEvent
    enabled: HookFlagConfiguration[bool]
    wait_time: HookFlagConfiguration[int]
    hooks: Sequence[LoadedHookConfiguration]


class SingleEventConfiguration(TypedDict):
    """Configuration for a single event"""

    enabled: bool | None
    wait_time: int | None


class HookConfiguration(TypedDict):
    """Hook configuration as stored in the global/project configuration JSON files"""

    all: SingleEventConfiguration  # defaults for all events
    events: dict[str, SingleEventConfiguration]


class ClickStyleFunction(Protocol):
    """A function to style CLI output. The definition is from Click."""

    def __call__(
        self,
        text: Any,
        fg: int | tuple[int, int, int] | str | None = None,
        bg: int | tuple[int, int, int] | str | None = None,
        bold: bool | None = None,
        dim: bool | None = None,
        underline: bool | None = None,
        overline: bool | None = None,
        italic: bool | None = None,
        blink: bool | None = None,
        reverse: bool | None = None,
        strikethrough: bool | None = None,
        reset: bool = True,
    ) -> str:
        pass


class HookManager:
    """Manages the state of loaded hooks & event configuration (are events enabled, etc.)"""

    config: Config
    cli_echo: Callable[[str], None]  # Command to print to the CLI
    cli_style: ClickStyleFunction  # Command to style a CLI output
    _global_hookconfig: HookConfiguration | None
    _project_hookconfig: HookConfiguration | None

    def __init__(
        self,
        config: Config,
        *,
        # To not have a dependency on Click in riptide-lib, these functions are injected.
        # If not given, normal print without styling is used.
        cli_echo: Callable[[str], None] | None = None,
        cli_style: ClickStyleFunction | None = None,
    ) -> None:
        self.config = config
        if cli_echo is None:
            cli_echo = print
        if cli_style is None:
            cli_style = lambda text, *args, **kwargs: text  # noqa: E731
        self.cli_echo = cli_echo
        self.cli_style = cli_style
        self._global_hookconfig = None
        self._project_hookconfig = None

    @property
    def global_hookconfig(self) -> HookConfiguration:
        if self._global_hookconfig is None:
            try:
                with open(riptide_hooks_config_file()) as f:
                    self._global_hookconfig = json.load(f)
            except FileNotFoundError:
                self._global_hookconfig = empty_hookconfig()
        return self._global_hookconfig

    @property
    def project_hookconfig(self) -> HookConfiguration:
        if self._project_hookconfig is None:
            try:
                with open(get_project_hooks_config_file_path(self.config["project"].folder()), encoding="utf-8") as f:
                    self._project_hookconfig = json.load(f)
            except (FileNotFoundError, KeyError):
                self._project_hookconfig = empty_hookconfig()
        return self._project_hookconfig

    def get_current_configuration(self) -> tuple[ApplicableEventConfiguration, Sequence[ApplicableEventConfiguration]]:
        """Returns current defaults (first tuple element) and individual event configurations."""
        events = []
        global_hooks = self.global_hooks()
        project_hooks = self.project_hooks()

        for event in HookEvent:
            events.append(self._get_event_config(global_hooks, project_hooks, event))

        # Also collect custom events
        for hook in itertools.chain(global_hooks.values(), project_hooks.values()):
            for any_event in hook.events:
                if HookEvent.is_custom(any_event):
                    if any_event not in events:
                        events.append(self._get_event_config(global_hooks, project_hooks, any_event))

        global_enabled = self.global_hookconfig["all"]["enabled"]
        global_enabled_effective = global_enabled if global_enabled is not None else False
        project_enabled = self.project_hookconfig["all"]["enabled"]
        project_enabled_effective = project_enabled if project_enabled is not None else True
        global_wait_time = self.global_hookconfig["all"]["wait_time"]
        project_wait_time = self.project_hookconfig["all"]["wait_time"]
        defaults: ApplicableEventConfiguration = {
            "event": "_default",
            "enabled": {
                "effective": global_enabled_effective and project_enabled_effective,
                "default": global_enabled,
                "project": project_enabled,
            },
            "wait_time": {
                "effective": (project_wait_time if project_wait_time is not None else global_wait_time) or 0,
                "default": global_wait_time,
                "project": project_wait_time,
            },
            "hooks": [],
        }

        return defaults, events

    def global_hooks(self) -> Mapping[str, Hook]:
        return self.config["hooks"]

    def project_hooks(self) -> Mapping[str, Hook]:
        if "project" in self.config:
            return self.config["project"]["app"]["hooks"]
        return {}

    def setup(self):
        """Initialize hook configuration files and external hooks"""
        if not os.path.exists(riptide_hooks_config_file()):
            self._init_hookconfig_file(riptide_hooks_config_file())
        if "project" in self.config:
            path = get_project_hooks_config_file_path(self.config["project"].folder())
            if not os.path.exists(path):
                self._init_hookconfig_file(path)
            self._setup_githooks()

    def trigger_event_on_cli(self, event: AnyHookEvent):
        """Trigger an event, run hooks and output current status"""
        raise NotImplementedError()

    def get_applicable_hooks_for(self, event: AnyHookEvent) -> Sequence[tuple[bool, str, Hook]]:
        """
        Returns list of applicable hooks (enabled and defined hooks for the given event).

        The boolean flag in the returned tuples is False for global-defined hooks and True for project hooks.
        """
        if not self._is_event_enabled(event):
            return []
        events = []
        for key, hook in self.global_hooks().items():
            events.append((False, key, hook))
        for key, hook in self.project_hooks().items():
            events.append((True, key, hook))
        return events

    def configure_event(
        self, event: AnyHookEvent | None, use_default: bool, enable_value: bool | None, wait_timeout_value: int | None
    ):
        config = self.global_hookconfig if use_default else self.project_hookconfig
        if event is None:
            if enable_value is not None:
                config["all"]["enabled"] = enable_value
            if wait_timeout_value is not None:
                config["all"]["wait_time"] = wait_timeout_value
        else:
            event_key = HookEvent.key_for(event)
            if event_key in config["events"]:
                if enable_value is not None:
                    config["events"][event_key]["enabled"] = enable_value
                if wait_timeout_value is not None:
                    config["events"][event_key]["wait_time"] = wait_timeout_value
            else:
                config["events"][event_key] = {"enabled": enable_value, "wait_time": wait_timeout_value}
        path = (
            riptide_hooks_config_file()
            if use_default
            else get_project_hooks_config_file_path(self.config["project"].folder())
        )
        self._save_hookconfig(path, config)

    def _setup_githooks(self):
        for event in HookEvent.git_events():
            if len(self.get_applicable_hooks_for(event)) > 0:
                self._setup_githook(event)

    def _setup_githook(self, event: HookEvent):
        git_event_name = event.key.removeprefix("git-")
        git_hook_file = os.path.join(self.config["project"].folder(), ".git", "hooks", git_event_name)
        riptide_config_lines = self._git_hook_trigger_lines(event)
        if not os.path.exists(git_hook_file):
            with open(git_hook_file, "w") as f:
                f.writelines(["#!/bin/sh\n"] + riptide_config_lines)
            st = os.stat(git_hook_file)
            os.chmod(git_hook_file, st.st_mode | stat.S_IEXEC)
        else:
            with open(git_hook_file, "r") as f:
                hook_content = f.read()
            if GITHOOK_NEEDLE_RIPTIDE_HOOKS not in hook_content:
                with open(git_hook_file, "a") as f:
                    f.writelines(riptide_config_lines)

    def _get_event_config(
        self, global_hooks: Mapping[str, Hook], project_hooks: Mapping[str, Hook], event: AnyHookEvent
    ) -> ApplicableEventConfiguration:
        event_hooks: list[LoadedHookConfiguration] = []
        for hook_key, hook in global_hooks.items():
            if event in hook.events:
                event_hooks.append({"key": hook_key, "hook": hook, "defined_in": "default"})
        for hook_key, hook in project_hooks.items():
            if event in hook.events:
                event_hooks.append({"key": hook_key, "hook": hook, "defined_in": "project"})
        return {
            "event": event,
            "enabled": {
                "effective": self._is_event_enabled(event),
                "default": self._event_config_default(event)["enabled"],
                "project": self._event_config_project(event)["enabled"],
            },
            "wait_time": {
                "effective": self._get_event_wait_time(event),
                "default": self._event_config_default(event)["wait_time"],
                "project": self._event_config_project(event)["wait_time"],
            },
            "hooks": event_hooks,
        }

    def _is_event_enabled(self, event: AnyHookEvent, print_warning_if_not_defined: bool = False) -> bool:
        global_value = self._event_config_default(event, True)["enabled"]
        global_value_was_none = False
        if global_value is None:
            global_value_was_none = True
            global_value = False
        project_value = self._event_config_project(event, True)["enabled"]
        if project_value is None:
            project_value = True
            if global_value_was_none and print_warning_if_not_defined:
                self.cli_echo(
                    self.cli_style("Riptide Warning: ", fg="yellow", bold=True)
                    + self.cli_style(hook_not_configured_warning(HookEvent.key_for(event)), fg="yellow")
                )

        return global_value and project_value

    def _get_event_wait_time(self, event: AnyHookEvent) -> int:
        project_value = self._event_config_project(event, True)["wait_time"]
        if project_value is not None:
            return project_value
        return self._event_config_default(event, True)["wait_time"] or 0

    def _event_config_default(self, event: AnyHookEvent, merge_with_all: bool = False) -> SingleEventConfiguration:
        event_key = HookEvent.key_for(event)
        if event_key in self.global_hookconfig["events"]:
            if merge_with_all:
                return merge_config(self.global_hookconfig["all"], self.global_hookconfig["events"][event_key])
            else:
                return self.global_hookconfig["events"][event_key]
        if merge_with_all:
            return self.global_hookconfig["all"]
        else:
            return {"enabled": None, "wait_time": None}

    def _event_config_project(self, event: AnyHookEvent, merge_with_all: bool = False) -> SingleEventConfiguration:
        event_key = HookEvent.key_for(event)
        if event_key in self.project_hookconfig["events"]:
            if merge_with_all:
                return merge_config(self.project_hookconfig["all"], self.project_hookconfig["events"][event_key])
            else:
                return self.project_hookconfig["events"][event_key]
        if merge_with_all:
            return self.project_hookconfig["all"]
        else:
            return {"enabled": None, "wait_time": None}

    @classmethod
    def _init_hookconfig_file(cls, path: str):
        cls._save_hookconfig(path, empty_hookconfig())

    @classmethod
    def _save_hookconfig(cls, path, config: HookConfiguration):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f)

    @staticmethod
    def _git_hook_trigger_lines(event: HookEvent) -> list[str]:
        return [
            "\n",
            (
                GITHOOK_NEEDLE_RIPTIDE_HOOKS
                + " - Do not modify or remove this line or the next lines. You can move them around.\n"
            ),
            "### If you want to disable Riptide hooks, run `riptide hook-configure`.\n",
            "riptide hook-trigger " + event.key + "\n",
            "### RIPTIDE HOOK CONFIG END\n",
        ]


def empty_hookconfig() -> HookConfiguration:
    return {"all": {"enabled": None, "wait_time": None}, "events": {}}


def hook_not_configured_warning(event_key: str):
    return (
        f"Riptide has hooks defined for this action. They are not run by default for security reasons.\n"
        f"To disable this warning, please configure your choice for hooks globally:\n"
        f"    riptide hook-configure -g --enable=true/false\n"
        f"\n"
        f"You can also configure your choice specifically for this project:\n"
        f"    riptide hook-configure --enable=true/false\n"
        f"Additionally you can configure what should happen for this event specifically\n"
        f"    riptide hook-configure [-g] --enable=true/false {event_key}\n"
        f"\n"
        f"Please see the Riptide documentation for more information."
    )


def merge_config(a: SingleEventConfiguration, b: SingleEventConfiguration) -> SingleEventConfiguration:
    """Merge two configurations. If for `b` a value is `None`, the value from `a` is used."""
    if a["enabled"] is None:
        a["enabled"] = b["enabled"]
    if a["wait_time"] is None:
        a["wait_time"] = b["wait_time"]
    return b
