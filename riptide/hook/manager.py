from __future__ import annotations

import itertools
import json
import os
import stat
import sys
from time import sleep
from typing import (
    IO,
    Any,
    Generic,
    Literal,
    Mapping,
    Sequence,
    TypeAlias,
    TypedDict,
    TypeVar,
)

from riptide.config.document.config import Config
from riptide.config.document.hook import Hook
from riptide.config.files import (
    get_project_hooks_config_file_path,
    riptide_hooks_config_file,
)
from riptide.engine.abstract import AbstractEngine, SimpleBindVolume
from riptide.hook.additional_volumes import HookHostPathArgument, apply_hook_mounts
from riptide.hook.cli import DefaultHookCliDisplay, HookCliDisplay
from riptide.hook.event import AnyHookEvent, HookEvent
from riptide.plugin.abstract import AbstractPlugin
from riptide.plugin.loader import load_plugins

HookArgument: TypeAlias = str | HookHostPathArgument

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


class HookManager:
    """Manages the state of loaded hooks & event configuration (are events enabled, etc.)"""

    config: Config
    engine: AbstractEngine
    cli: HookCliDisplay  # Adapter to print to the CLI
    _global_hookconfig: HookConfiguration | None
    _project_hookconfig: HookConfiguration | None

    def __init__(
        self,
        config: Config,
        engine: AbstractEngine,
        *,
        # To not have a dependency on rich in riptide-lib, the CLI printing functionality is injected
        # If not given, a fallback print-based implementation is loaded.
        cli: HookCliDisplay | None = None,
    ) -> None:
        self.config = config
        self.engine = engine
        if cli is None:
            cli = DefaultHookCliDisplay()
        self.cli = cli
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
        already_collected = set()
        for hook in itertools.chain(global_hooks.values(), project_hooks.values()):
            for any_event in hook.events:
                if HookEvent.is_custom(any_event):
                    if any_event not in events and any_event not in already_collected:
                        events.append(self._get_event_config(global_hooks, project_hooks, any_event))
                        already_collected.add(any_event)

        global_enabled = self.global_hookconfig["all"]["enabled"]
        project_enabled = self.project_hookconfig["all"]["enabled"]
        effective_enabled = False
        if project_enabled is not None:
            effective_enabled = project_enabled
        elif global_enabled is not None:
            effective_enabled = global_enabled
        global_wait_time = self.global_hookconfig["all"]["wait_time"]
        project_wait_time = self.project_hookconfig["all"]["wait_time"]
        defaults: ApplicableEventConfiguration = {
            "event": "_default",
            "enabled": {
                "effective": effective_enabled,
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

    def trigger_event_on_cli(
        self,
        event: AnyHookEvent,
        args: Sequence[HookArgument],
        additional_host_mounts: dict[str, HookHostPathArgument],  # container path -> host path + ro flag
    ) -> int:
        """Trigger an event, run hooks and output current status. Returns exit code. Returns -1 if no hook was run."""
        event_key = HookEvent.key_for(event)
        args_for_containers, extra_mounts = apply_hook_mounts(self.config, args, additional_host_mounts)
        args_for_plugins = [str(a) for a in args]
        hooks = self.get_applicable_hooks_for(event, print_warning_if_not_defined=True)
        if len(hooks) > 0:
            wait_time = self._get_event_wait_time(event)
            if wait_time > 0:
                self.cli.will_run_hook(event_key, wait_time)
                try:
                    still_waiting_for = wait_time
                    while still_waiting_for > 0:
                        self.cli.will_run_hook_tick()
                        sleep(1)
                        still_waiting_for -= 1
                    self.cli.after_will_run_hook()
                except KeyboardInterrupt:
                    self.cli.after_will_run_hook()
                    self.cli.system_info("Hooks skipped.")
                    return 0

            for from_project, key, hook in hooks:
                if isinstance(hook, AbstractPlugin):
                    ret = hook.event_triggered(self.config, event, args_for_plugins)
                    if ret != 0:
                        return ret
                else:
                    hook_desc = key
                    if not from_project:
                        hook_desc += " (from global)"

                    if "project" not in self.config:
                        self.cli.system_warn(f"Skipped running hook {hook_desc} since no project is loaded.")
                    else:
                        self.cli.hook_execution_begin(event_key, hook_desc)
                        ret = self.run_hook_on_cli(hook, args_for_containers, extra_mounts)
                        if ret != 0:
                            if hook.continue_on_error():
                                self.cli.hook_execution_end(event_key, hook_desc, "warn")
                            else:
                                self.cli.hook_execution_end(event_key, hook_desc, False)
                                return ret
                        else:
                            self.cli.hook_execution_end(event_key, hook_desc, True)
            return 0

        return -1

    def run_hook_on_cli(self, hook: Hook, args: Sequence[str], extra_volumes: dict[str, SimpleBindVolume]) -> int:
        return self.engine.cmd(
            hook.command(), hook.args(args), working_directory=hook.get_working_directory(), extra_volumes=extra_volumes
        )

    def get_applicable_hooks_for(
        self,
        event: AnyHookEvent,
        *,
        # Default value if neither globally nor in the project any enabled state is defined
        if_not_defined_set_enabled_to: bool = False,
        # Print a warning for the user if no enabled state is defined
        print_warning_if_not_defined: bool = False,
    ) -> Sequence[tuple[bool, str, Hook | AbstractPlugin]]:
        """
        Returns list of applicable hooks (enabled and defined hooks for the given event) or plugins that respond
        to the given event.

        The boolean flag in the returned tuples is False for global-defined hooks and True for project hooks.
        """
        event_enabled = True
        if not self._is_event_enabled(
            event,
            if_not_defined_set_enabled_to=if_not_defined_set_enabled_to,
        ):
            if not print_warning_if_not_defined:
                return []
            event_enabled = False
        events: list[tuple[bool, str, Hook | AbstractPlugin]] = []
        for key, hook in self.global_hooks().items():
            if event in hook.events:
                events.append((False, key, hook))
        for key, hook in self.project_hooks().items():
            if event in hook.events:
                events.append((True, key, hook))
        # Add plugins
        for plugin in load_plugins().values():
            if plugin.responds_to_event(event):
                events.append((False, "", plugin))
        if event_enabled:
            return events
        else:
            if len(events) > 0:
                global_value = self._event_config_default(event, True)["enabled"]
                project_value = self._event_config_project(event, True)["enabled"]
                if global_value is None and project_value is None:
                    self.cli.system_warn(hook_not_configured_warning(HookEvent.key_for(event)))
            return []

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
            # if_not_defined_set_enabled_to:
            # If global hook state is not defined, pretend the global hook state defaults to enabled
            # so that we still generate the git hook files, even if hooks would not run. This will cause
            # Riptide to then echo a warning when users trigger the git hook prompting the user to
            # please configure their enabled setting.
            if len(self.get_applicable_hooks_for(event, if_not_defined_set_enabled_to=True)) > 0:
                self._setup_githook(event)

    def _setup_githook(self, event: HookEvent):
        git_event_name = event.key.removeprefix("git-")
        git_hook_file = os.path.join(self.config["project"].folder(), ".git", "hooks", git_event_name)
        riptide_config_lines = self._git_hook_trigger_lines(event)
        if not os.path.exists(git_hook_file):
            with open(git_hook_file, "w") as f:
                f.writelines(["#!/bin/sh\n", "set -em\n"] + riptide_config_lines)
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

    def _is_event_enabled(
        self,
        event: AnyHookEvent,
        *,
        # Default value if neither globally nor in the project any enabled state is defined
        if_not_defined_set_enabled_to: bool = False,
    ) -> bool:
        global_value = self._event_config_default(event, True)["enabled"]
        project_value = self._event_config_project(event, True)["enabled"]
        if project_value is None:
            if global_value is None:
                return if_not_defined_set_enabled_to
            return global_value
        return project_value

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
            "riptide hook-trigger --mount-host-paths " + event.key + ' "$@"\n',
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
        f"Additionally you can configure what should happen for this event specifically:\n"
        f"    riptide hook-configure [-g] --enable=true/false {event_key}\n"
        f"\n"
        f"Please see the Riptide documentation for more information."
    )


def merge_config(a: SingleEventConfiguration, b: SingleEventConfiguration) -> SingleEventConfiguration:
    """Merge two configurations. If for `b` a value is `None`, the value from `a` is used."""
    a = dict(a)  # type: ignore
    if b["enabled"] is not None:
        a["enabled"] = b["enabled"]
    if b["wait_time"] is not None:
        a["wait_time"] = b["wait_time"]
    return a


def basic_echo(
    message: Any | None = None,
    file: IO[Any] | None = None,
    nl: bool = True,
    err: bool = False,
    color: bool | None = None,
):
    sep = "\n" if nl else ""
    if file is None and err:
        file = sys.stderr
    print(message, file=file, sep=sep)
