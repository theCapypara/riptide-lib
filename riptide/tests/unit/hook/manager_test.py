import json
import os
import sys
import unittest
from contextlib import contextmanager
from typing import Literal, Sequence
from unittest.mock import MagicMock

from riptide.config.document.command import Command
from riptide.config.document.config import Config
from riptide.config.document.hook import Hook
from riptide.config.document.project import Project
from riptide.engine.abstract import AbstractEngine
from riptide.hook.event import HookEvent
from riptide.hook.manager import (
    ApplicableEventConfiguration,
    HookManager,
    LoadedHookConfiguration,
)
from riptide.plugin.abstract import AbstractPlugin
from riptide.tests.helpers import get_fixture_path

FIXTURE_BASE_PATH = "hook_manager" + os.sep


def loaded_hook(
    key: str, events: list[str], image: str, command: str, defined_in: Literal["default"] | Literal["project"]
) -> LoadedHookConfiguration:
    command_obj = Command.from_dict({"command": command, "image": image})
    command_obj.freeze()
    hook_obj = Hook.from_dict({"events": events, "$name": key, "command": {"run": command_obj}})
    hook_obj.freeze()

    return {"key": key, "hook": hook_obj, "defined_in": defined_in}


GLOB_EN_PROJ_EN_HOOKS = [
    loaded_hook(
        "global-glob_en-proj_en",
        ["custom-glob-en-proj-en", "git-pre-commit"],
        "fooG",
        "fooG1",
        "default",
    ),
    loaded_hook("proj-glob_en-proj_en", ["custom-glob-en-proj-en", "pre-start"], "foo1", "foo11", "project"),
]

GLOB_DI_PROJ_EN_HOOKS = [
    loaded_hook("global-glob_di-proj_en", ["custom-glob-di-proj-en"], "foo", "foo", "default"),
    loaded_hook("proj-glob_di-proj_en", ["custom-glob-di-proj-en"], "foo2", "foo22", "project"),
]

GLOB_EN_PROJ_DI_HOOKS = [
    loaded_hook("global-glob_en-proj_di", ["custom-glob-en-proj-di"], "foo", "foo", "default"),
    loaded_hook("proj-glob_en-proj_di", ["custom-glob-en-proj-di"], "foo3", "foo33", "project"),
]

GLOB_DI_PROJ_DI_HOOKS = [
    loaded_hook("global-glob_di-proj_di", ["custom-glob-di-proj-di"], "foo", "foo", "default"),
    loaded_hook("proj-glob_di-proj_di", ["custom-glob-di-proj-di", "pre-db-import"], "foo4", "foo44", "project"),
]

GLOB_UN_PROJ_EN_HOOKS = [
    loaded_hook("global-glob_un-proj_en", ["custom-glob-un-proj-en"], "foo", "foo", "default"),
    loaded_hook("proj-glob_un-proj_en", ["custom-glob-un-proj-en"], "foo", "foo", "project"),
]

GLOB_UN_PROJ_DI_HOOKS = [
    loaded_hook("global-glob_un-proj_di", ["custom-glob-un-proj-di"], "foo", "foo", "default"),
    loaded_hook("proj-glob_un-proj_di", ["custom-glob-un-proj-di"], "foo", "foo", "project"),
]

GLOB_UN_PROJ_UN_HOOKS = [
    loaded_hook("global-glob_un-proj_un", ["custom-glob-un-proj-un"], "foo", "foo", "default"),
    loaded_hook("proj-glob_un-proj_un", ["custom-glob-un-proj-un"], "foo", "foo", "project"),
]

GLOB_EN_PROJ_UN_HOOKS = [
    loaded_hook("global-glob_en-proj_un", ["custom-glob-en-proj-un"], "foo", "foo", "default"),
    loaded_hook("proj-glob_en-proj_un", ["custom-glob-en-proj-un"], "foo", "foo", "project"),
]

GLOB_DI_PROJ_UN_HOOKS = [
    loaded_hook("global-glob_di-proj_un", ["custom-glob-di-proj-un"], "foo", "foo", "default"),
    loaded_hook("proj-glob_di-proj_un", ["custom-glob-di-proj-un"], "foo", "foo", "project"),
]

GIT_PRE_COMMIT_HOOKS = [
    loaded_hook(
        "global-glob_en-proj_en",
        ["custom-glob-en-proj-en", "git-pre-commit"],
        "fooG",
        "fooG1",
        "default",
    )
]

PRE_START_HOOKS = [
    loaded_hook("proj-glob_en-proj_en", ["custom-glob-en-proj-en", "pre-start"], "foo1", "foo11", "project")
]

PRE_DB_IMPORT_HOOKS = [
    loaded_hook("proj-glob_di-proj_di", ["custom-glob-di-proj-di", "pre-db-import"], "foo4", "foo44", "project")
]


class HookManagerTestCase(unittest.TestCase):
    maxDiff = 30000

    config: Config
    engine: MagicMock | AbstractEngine
    subject: HookManager

    def setUp(self):
        self.config = Config.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "system_config.yml"))
        project = Project.from_dict(self.config.internal_get("project"))
        project.resolve_and_merge_references([])
        self.config.internal_set("project", project)
        self.config.resolve_and_merge_references([])
        self.config.validate()
        self.config.freeze()
        self.engine = MagicMock(spec=AbstractEngine)
        self.subject = HookManager(self.config, self.engine)
        # These are loaded by the tests when using with self.hookconfigs(...)
        self.subject._global_hookconfig = NotImplemented
        self.subject._project_hookconfig = NotImplemented

    def test_get_current_configuration_global_un_project_un(self):
        expected_default = {
            "event": "_default",
            "enabled": {
                "effective": False,
                "default": None,
                "project": None,
            },
            "wait_time": {
                "effective": 0,
                "default": None,
                "project": None,
            },
            "hooks": [],
        }
        expected_per_event = [
            {
                "event": "custom-glob-en-proj-en",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": True,
                },
                "wait_time": {
                    "effective": 20,
                    "default": None,
                    "project": 20,
                },
                "hooks": GLOB_EN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-en",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": True,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-di",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": False,
                },
                "wait_time": {
                    "effective": 80,
                    "default": 0,
                    "project": 80,
                },
                "hooks": GLOB_EN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-di",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": False,
                },
                "wait_time": {
                    "effective": 10,
                    "default": 10,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-en",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": True,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-di",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": False,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-un",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-un",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_EN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-un",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": None,
                },
                "wait_time": {
                    "effective": 20,
                    "default": 20,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_UN_HOOKS,
            },
            {
                "event": HookEvent.GitPreCommit,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GIT_PRE_COMMIT_HOOKS,
            },
            {
                "event": HookEvent.PreStart,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_START_HOOKS,
            },
            {
                "event": HookEvent.PreDbImport,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_DB_IMPORT_HOOKS,
            },
        ] + [
            {
                "event": event,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": [],
            }
            for event in HookEvent
            if event not in [HookEvent.GitPreCommit, HookEvent.PreStart, HookEvent.PreDbImport]
        ]
        with self.hookconfigs(
            "global_hookconfig_default_unconfigured.json", "project_hookconfig_default_unconfigured.json"
        ):
            result_default, result_per_event = self.subject.get_current_configuration()
            self.assertDictEqual(expected_default, result_default)
            self.assertPerEventsEqual(expected_per_event, result_per_event)  # type: ignore

    def test_get_current_configuration_global_en_project_un(self):
        expected_default = {
            "event": "_default",
            "enabled": {
                "effective": True,
                "default": True,
                "project": None,
            },
            "wait_time": {
                "effective": 0,
                "default": None,
                "project": None,
            },
            "hooks": [],
        }
        expected_per_event = [
            {
                "event": "custom-glob-en-proj-en",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": True,
                },
                "wait_time": {
                    "effective": 20,
                    "default": None,
                    "project": 20,
                },
                "hooks": GLOB_EN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-en",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": True,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-di",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": False,
                },
                "wait_time": {
                    "effective": 80,
                    "default": 0,
                    "project": 80,
                },
                "hooks": GLOB_EN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-di",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": False,
                },
                "wait_time": {
                    "effective": 10,
                    "default": 10,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-en",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": True,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-di",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": False,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-un",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-un",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_EN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-un",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": None,
                },
                "wait_time": {
                    "effective": 20,
                    "default": 20,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_UN_HOOKS,
            },
            {
                "event": HookEvent.GitPreCommit,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GIT_PRE_COMMIT_HOOKS,
            },
            {
                "event": HookEvent.PreStart,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_START_HOOKS,
            },
            {
                "event": HookEvent.PreDbImport,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_DB_IMPORT_HOOKS,
            },
        ] + [
            {
                "event": event,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": [],
            }
            for event in HookEvent
            if event not in [HookEvent.GitPreCommit, HookEvent.PreStart, HookEvent.PreDbImport]
        ]

        with self.hookconfigs("global_hookconfig_default_enabled.json", "project_hookconfig_default_unconfigured.json"):
            result_default, result_per_event = self.subject.get_current_configuration()
            self.assertDictEqual(expected_default, result_default)
            self.assertPerEventsEqual(expected_per_event, result_per_event)  # type: ignore

    def test_get_current_configuration_global_di_project_un(self):
        expected_default = {
            "event": "_default",
            "enabled": {
                "effective": False,
                "default": False,
                "project": None,
            },
            "wait_time": {
                "effective": 900,
                "default": 900,
                "project": None,
            },
            "hooks": [],
        }
        expected_per_event = [
            {
                "event": "custom-glob-en-proj-en",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": True,
                },
                "wait_time": {
                    "effective": 20,
                    "default": None,
                    "project": 20,
                },
                "hooks": GLOB_EN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-en",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": True,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-di",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": False,
                },
                "wait_time": {
                    "effective": 80,
                    "default": 0,
                    "project": 80,
                },
                "hooks": GLOB_EN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-di",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": False,
                },
                "wait_time": {
                    "effective": 10,
                    "default": 10,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-en",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": True,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-di",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": False,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-un",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-un",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_EN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-un",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": None,
                },
                "wait_time": {
                    "effective": 20,
                    "default": 20,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_UN_HOOKS,
            },
            {
                "event": HookEvent.GitPreCommit,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GIT_PRE_COMMIT_HOOKS,
            },
            {
                "event": HookEvent.PreStart,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_START_HOOKS,
            },
            {
                "event": HookEvent.PreDbImport,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_DB_IMPORT_HOOKS,
            },
        ] + [
            {
                "event": event,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": [],
            }
            for event in HookEvent
            if event not in [HookEvent.GitPreCommit, HookEvent.PreStart, HookEvent.PreDbImport]
        ]
        with self.hookconfigs(
            "global_hookconfig_default_disabled.json", "project_hookconfig_default_unconfigured.json"
        ):
            result_default, result_per_event = self.subject.get_current_configuration()
            self.assertDictEqual(expected_default, result_default)
            self.assertPerEventsEqual(expected_per_event, result_per_event)  # type: ignore

    def test_get_current_configuration_global_un_project_en(self):
        expected_default = {
            "event": "_default",
            "enabled": {
                "effective": True,
                "default": None,
                "project": True,
            },
            "wait_time": {
                "effective": 999,
                "default": None,
                "project": 999,
            },
            "hooks": [],
        }
        expected_per_event = [
            {
                "event": "custom-glob-en-proj-en",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": True,
                },
                "wait_time": {
                    "effective": 20,
                    "default": None,
                    "project": 20,
                },
                "hooks": GLOB_EN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-en",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": True,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-di",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": False,
                },
                "wait_time": {
                    "effective": 80,
                    "default": 0,
                    "project": 80,
                },
                "hooks": GLOB_EN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-di",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": False,
                },
                "wait_time": {
                    "effective": 999,
                    "default": 10,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-en",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": True,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-di",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": False,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-un",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-un",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_EN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-un",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": 20,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_UN_HOOKS,
            },
            {
                "event": HookEvent.GitPreCommit,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GIT_PRE_COMMIT_HOOKS,
            },
            {
                "event": HookEvent.PreStart,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_START_HOOKS,
            },
            {
                "event": HookEvent.PreDbImport,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_DB_IMPORT_HOOKS,
            },
        ] + [
            {
                "event": event,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": [],
            }
            for event in HookEvent
            if event not in [HookEvent.GitPreCommit, HookEvent.PreStart, HookEvent.PreDbImport]
        ]
        with self.hookconfigs("global_hookconfig_default_unconfigured.json", "project_hookconfig_default_enabled.json"):
            result_default, result_per_event = self.subject.get_current_configuration()
            self.assertDictEqual(expected_default, result_default)
            self.assertPerEventsEqual(expected_per_event, result_per_event)  # type: ignore

    def test_get_current_configuration_global_en_project_en(self):
        expected_default = {
            "event": "_default",
            "enabled": {
                "effective": True,
                "default": True,
                "project": True,
            },
            "wait_time": {
                "effective": 999,
                "default": None,
                "project": 999,
            },
            "hooks": [],
        }
        expected_per_event = [
            {
                "event": "custom-glob-en-proj-en",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": True,
                },
                "wait_time": {
                    "effective": 20,
                    "default": None,
                    "project": 20,
                },
                "hooks": GLOB_EN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-en",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": True,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-di",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": False,
                },
                "wait_time": {
                    "effective": 80,
                    "default": 0,
                    "project": 80,
                },
                "hooks": GLOB_EN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-di",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": False,
                },
                "wait_time": {
                    "effective": 999,
                    "default": 10,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-en",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": True,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-di",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": False,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-un",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-un",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_EN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-un",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": 20,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_UN_HOOKS,
            },
            {
                "event": HookEvent.GitPreCommit,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GIT_PRE_COMMIT_HOOKS,
            },
            {
                "event": HookEvent.PreStart,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_START_HOOKS,
            },
            {
                "event": HookEvent.PreDbImport,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_DB_IMPORT_HOOKS,
            },
        ] + [
            {
                "event": event,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": [],
            }
            for event in HookEvent
            if event not in [HookEvent.GitPreCommit, HookEvent.PreStart, HookEvent.PreDbImport]
        ]
        with self.hookconfigs("global_hookconfig_default_enabled.json", "project_hookconfig_default_enabled.json"):
            result_default, result_per_event = self.subject.get_current_configuration()
            self.assertDictEqual(expected_default, result_default)
            self.assertPerEventsEqual(expected_per_event, result_per_event)  # type: ignore

    def test_get_current_configuration_global_di_project_en(self):
        expected_default = {
            "event": "_default",
            "enabled": {
                "effective": True,
                "default": False,
                "project": True,
            },
            "wait_time": {
                "effective": 999,
                "default": 900,
                "project": 999,
            },
            "hooks": [],
        }
        expected_per_event = [
            {
                "event": "custom-glob-en-proj-en",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": True,
                },
                "wait_time": {
                    "effective": 20,
                    "default": None,
                    "project": 20,
                },
                "hooks": GLOB_EN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-en",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": True,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-di",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": False,
                },
                "wait_time": {
                    "effective": 80,
                    "default": 0,
                    "project": 80,
                },
                "hooks": GLOB_EN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-di",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": False,
                },
                "wait_time": {
                    "effective": 999,
                    "default": 10,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-en",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": True,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-di",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": False,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-un",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-un",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_EN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-un",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": 20,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_UN_HOOKS,
            },
            {
                "event": HookEvent.GitPreCommit,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": GIT_PRE_COMMIT_HOOKS,
            },
            {
                "event": HookEvent.PreStart,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_START_HOOKS,
            },
            {
                "event": HookEvent.PreDbImport,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_DB_IMPORT_HOOKS,
            },
        ] + [
            {
                "event": event,
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 999,
                    "default": None,
                    "project": None,
                },
                "hooks": [],
            }
            for event in HookEvent
            if event not in [HookEvent.GitPreCommit, HookEvent.PreStart, HookEvent.PreDbImport]
        ]
        with self.hookconfigs("global_hookconfig_default_disabled.json", "project_hookconfig_default_enabled.json"):
            result_default, result_per_event = self.subject.get_current_configuration()
            self.assertDictEqual(expected_default, result_default)
            self.assertPerEventsEqual(expected_per_event, result_per_event)  # type: ignore

    def test_get_current_configuration_global_un_project_di(self):
        expected_default = {
            "event": "_default",
            "enabled": {
                "effective": False,
                "default": None,
                "project": False,
            },
            "wait_time": {
                "effective": 0,
                "default": None,
                "project": None,
            },
            "hooks": [],
        }
        expected_per_event = [
            {
                "event": "custom-glob-en-proj-en",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": True,
                },
                "wait_time": {
                    "effective": 20,
                    "default": None,
                    "project": 20,
                },
                "hooks": GLOB_EN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-en",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": True,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-di",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": False,
                },
                "wait_time": {
                    "effective": 80,
                    "default": 0,
                    "project": 80,
                },
                "hooks": GLOB_EN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-di",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": False,
                },
                "wait_time": {
                    "effective": 10,
                    "default": 10,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-en",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": True,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-di",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": False,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-un",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-un",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_EN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-un",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": None,
                },
                "wait_time": {
                    "effective": 20,
                    "default": 20,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_UN_HOOKS,
            },
            {
                "event": HookEvent.GitPreCommit,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GIT_PRE_COMMIT_HOOKS,
            },
            {
                "event": HookEvent.PreStart,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_START_HOOKS,
            },
            {
                "event": HookEvent.PreDbImport,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_DB_IMPORT_HOOKS,
            },
        ] + [
            {
                "event": event,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": [],
            }
            for event in HookEvent
            if event not in [HookEvent.GitPreCommit, HookEvent.PreStart, HookEvent.PreDbImport]
        ]
        with self.hookconfigs(
            "global_hookconfig_default_unconfigured.json", "project_hookconfig_default_disabled.json"
        ):
            result_default, result_per_event = self.subject.get_current_configuration()
            self.assertDictEqual(expected_default, result_default)
            self.assertPerEventsEqual(expected_per_event, result_per_event)  # type: ignore

    def test_get_current_configuration_global_en_project_di(self):
        expected_default = {
            "event": "_default",
            "enabled": {
                "effective": False,
                "default": True,
                "project": False,
            },
            "wait_time": {
                "effective": 0,
                "default": None,
                "project": None,
            },
            "hooks": [],
        }
        expected_per_event = [
            {
                "event": "custom-glob-en-proj-en",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": True,
                },
                "wait_time": {
                    "effective": 20,
                    "default": None,
                    "project": 20,
                },
                "hooks": GLOB_EN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-en",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": True,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-di",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": False,
                },
                "wait_time": {
                    "effective": 80,
                    "default": 0,
                    "project": 80,
                },
                "hooks": GLOB_EN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-di",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": False,
                },
                "wait_time": {
                    "effective": 10,
                    "default": 10,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-en",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": True,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-di",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": False,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-un",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-un",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_EN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-un",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": None,
                },
                "wait_time": {
                    "effective": 20,
                    "default": 20,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_UN_HOOKS,
            },
            {
                "event": HookEvent.GitPreCommit,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": GIT_PRE_COMMIT_HOOKS,
            },
            {
                "event": HookEvent.PreStart,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_START_HOOKS,
            },
            {
                "event": HookEvent.PreDbImport,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_DB_IMPORT_HOOKS,
            },
        ] + [
            {
                "event": event,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 0,
                    "default": None,
                    "project": None,
                },
                "hooks": [],
            }
            for event in HookEvent
            if event not in [HookEvent.GitPreCommit, HookEvent.PreStart, HookEvent.PreDbImport]
        ]
        with self.hookconfigs("global_hookconfig_default_enabled.json", "project_hookconfig_default_disabled.json"):
            result_default, result_per_event = self.subject.get_current_configuration()
            self.assertDictEqual(expected_default, result_default)
            self.assertPerEventsEqual(expected_per_event, result_per_event)  # type: ignore

    def test_get_current_configuration_global_di_project_di(self):
        expected_default = {
            "event": "_default",
            "enabled": {
                "effective": False,
                "default": False,
                "project": False,
            },
            "wait_time": {
                "effective": 900,
                "default": 900,
                "project": None,
            },
            "hooks": [],
        }
        expected_per_event = [
            {
                "event": "custom-glob-en-proj-en",
                "enabled": {
                    "effective": True,
                    "default": True,
                    "project": True,
                },
                "wait_time": {
                    "effective": 20,
                    "default": None,
                    "project": 20,
                },
                "hooks": GLOB_EN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-en",
                "enabled": {
                    "effective": True,
                    "default": False,
                    "project": True,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-di",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": False,
                },
                "wait_time": {
                    "effective": 80,
                    "default": 0,
                    "project": 80,
                },
                "hooks": GLOB_EN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-di",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": False,
                },
                "wait_time": {
                    "effective": 10,
                    "default": 10,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-en",
                "enabled": {
                    "effective": True,
                    "default": None,
                    "project": True,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_EN_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-di",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": False,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_DI_HOOKS,
            },
            {
                "event": "custom-glob-un-proj-un",
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_UN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-en-proj-un",
                "enabled": {
                    "effective": False,
                    "default": True,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GLOB_EN_PROJ_UN_HOOKS,
            },
            {
                "event": "custom-glob-di-proj-un",
                "enabled": {
                    "effective": False,
                    "default": False,
                    "project": None,
                },
                "wait_time": {
                    "effective": 20,
                    "default": 20,
                    "project": None,
                },
                "hooks": GLOB_DI_PROJ_UN_HOOKS,
            },
            {
                "event": HookEvent.GitPreCommit,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": GIT_PRE_COMMIT_HOOKS,
            },
            {
                "event": HookEvent.PreStart,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_START_HOOKS,
            },
            {
                "event": HookEvent.PreDbImport,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": PRE_DB_IMPORT_HOOKS,
            },
        ] + [
            {
                "event": event,
                "enabled": {
                    "effective": False,
                    "default": None,
                    "project": None,
                },
                "wait_time": {
                    "effective": 900,
                    "default": None,
                    "project": None,
                },
                "hooks": [],
            }
            for event in HookEvent
            if event not in [HookEvent.GitPreCommit, HookEvent.PreStart, HookEvent.PreDbImport]
        ]
        with self.hookconfigs("global_hookconfig_default_disabled.json", "project_hookconfig_default_disabled.json"):
            result_default, result_per_event = self.subject.get_current_configuration()
            self.assertDictEqual(expected_default, result_default)
            self.assertPerEventsEqual(expected_per_event, result_per_event)  # type: ignore

    def test_get_applicable_hooks_for_global_un_project_un(self):
        with self.hookconfigs(
            "global_hookconfig_default_unconfigured.json", "project_hookconfig_default_unconfigured.json"
        ):
            tstfn = self.subject.get_applicable_hooks_for
            self.assertApplHooksEq(GLOB_EN_PROJ_EN_HOOKS, tstfn("custom-glob-en-proj-en"))
            self.assertApplHooksEq(GLOB_DI_PROJ_EN_HOOKS, tstfn("custom-glob-di-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_EN_HOOKS, tstfn("custom-glob-un-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-un"))
            self.assertApplHooksEq(GLOB_EN_PROJ_UN_HOOKS, tstfn("custom-glob-en-proj-un"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-un"))
            self.assertApplHooksEq([], tstfn(HookEvent.GitPreCommit))
            self.assertApplHooksEq([], tstfn(HookEvent.PreStart))
            self.assertApplHooksEq([], tstfn(HookEvent.PreDbImport))

    def test_get_applicable_hooks_for_global_en_project_un(self):
        with self.hookconfigs("global_hookconfig_default_enabled.json", "project_hookconfig_default_unconfigured.json"):
            tstfn = self.subject.get_applicable_hooks_for
            self.assertApplHooksEq(GLOB_EN_PROJ_EN_HOOKS, tstfn("custom-glob-en-proj-en"))
            self.assertApplHooksEq(GLOB_DI_PROJ_EN_HOOKS, tstfn("custom-glob-di-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_EN_HOOKS, tstfn("custom-glob-un-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_UN_HOOKS, tstfn("custom-glob-un-proj-un"))
            self.assertApplHooksEq(GLOB_EN_PROJ_UN_HOOKS, tstfn("custom-glob-en-proj-un"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-un"))
            self.assertApplHooksEq(GIT_PRE_COMMIT_HOOKS, tstfn(HookEvent.GitPreCommit))
            self.assertApplHooksEq(PRE_START_HOOKS, tstfn(HookEvent.PreStart))
            self.assertApplHooksEq(PRE_DB_IMPORT_HOOKS, tstfn(HookEvent.PreDbImport))

    def test_get_applicable_hooks_for_global_di_project_un(self):
        with self.hookconfigs(
            "global_hookconfig_default_disabled.json", "project_hookconfig_default_unconfigured.json"
        ):
            tstfn = self.subject.get_applicable_hooks_for
            self.assertApplHooksEq(GLOB_EN_PROJ_EN_HOOKS, tstfn("custom-glob-en-proj-en"))
            self.assertApplHooksEq(GLOB_DI_PROJ_EN_HOOKS, tstfn("custom-glob-di-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_EN_HOOKS, tstfn("custom-glob-un-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-un"))
            self.assertApplHooksEq(GLOB_EN_PROJ_UN_HOOKS, tstfn("custom-glob-en-proj-un"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-un"))
            self.assertApplHooksEq([], tstfn(HookEvent.GitPreCommit))
            self.assertApplHooksEq([], tstfn(HookEvent.PreStart))
            self.assertApplHooksEq([], tstfn(HookEvent.PreDbImport))

    def test_get_applicable_hooks_for_global_un_project_en(self):
        with self.hookconfigs("global_hookconfig_default_unconfigured.json", "project_hookconfig_default_enabled.json"):
            tstfn = self.subject.get_applicable_hooks_for
            self.assertApplHooksEq(GLOB_EN_PROJ_EN_HOOKS, tstfn("custom-glob-en-proj-en"))
            self.assertApplHooksEq(GLOB_DI_PROJ_EN_HOOKS, tstfn("custom-glob-di-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_EN_HOOKS, tstfn("custom-glob-un-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_UN_HOOKS, tstfn("custom-glob-un-proj-un"))
            self.assertApplHooksEq(GLOB_EN_PROJ_UN_HOOKS, tstfn("custom-glob-en-proj-un"))
            self.assertApplHooksEq(GLOB_DI_PROJ_UN_HOOKS, tstfn("custom-glob-di-proj-un"))
            self.assertApplHooksEq(GIT_PRE_COMMIT_HOOKS, tstfn(HookEvent.GitPreCommit))
            self.assertApplHooksEq(PRE_START_HOOKS, tstfn(HookEvent.PreStart))
            self.assertApplHooksEq(PRE_DB_IMPORT_HOOKS, tstfn(HookEvent.PreDbImport))

    def test_get_applicable_hooks_for_global_en_project_en(self):
        with self.hookconfigs("global_hookconfig_default_enabled.json", "project_hookconfig_default_enabled.json"):
            tstfn = self.subject.get_applicable_hooks_for
            self.assertApplHooksEq(GLOB_EN_PROJ_EN_HOOKS, tstfn("custom-glob-en-proj-en"))
            self.assertApplHooksEq(GLOB_DI_PROJ_EN_HOOKS, tstfn("custom-glob-di-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_EN_HOOKS, tstfn("custom-glob-un-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_UN_HOOKS, tstfn("custom-glob-un-proj-un"))
            self.assertApplHooksEq(GLOB_EN_PROJ_UN_HOOKS, tstfn("custom-glob-en-proj-un"))
            self.assertApplHooksEq(GLOB_DI_PROJ_UN_HOOKS, tstfn("custom-glob-di-proj-un"))
            self.assertApplHooksEq(GIT_PRE_COMMIT_HOOKS, tstfn(HookEvent.GitPreCommit))
            self.assertApplHooksEq(PRE_START_HOOKS, tstfn(HookEvent.PreStart))
            self.assertApplHooksEq(PRE_DB_IMPORT_HOOKS, tstfn(HookEvent.PreDbImport))

    def test_get_applicable_hooks_for_global_di_project_en(self):
        with self.hookconfigs("global_hookconfig_default_disabled.json", "project_hookconfig_default_enabled.json"):
            tstfn = self.subject.get_applicable_hooks_for
            self.assertApplHooksEq(GLOB_EN_PROJ_EN_HOOKS, tstfn("custom-glob-en-proj-en"))
            self.assertApplHooksEq(GLOB_DI_PROJ_EN_HOOKS, tstfn("custom-glob-di-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_EN_HOOKS, tstfn("custom-glob-un-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_UN_HOOKS, tstfn("custom-glob-un-proj-un"))
            self.assertApplHooksEq(GLOB_EN_PROJ_UN_HOOKS, tstfn("custom-glob-en-proj-un"))
            self.assertApplHooksEq(GLOB_DI_PROJ_UN_HOOKS, tstfn("custom-glob-di-proj-un"))
            self.assertApplHooksEq(GIT_PRE_COMMIT_HOOKS, tstfn(HookEvent.GitPreCommit))
            self.assertApplHooksEq(PRE_START_HOOKS, tstfn(HookEvent.PreStart))
            self.assertApplHooksEq(PRE_DB_IMPORT_HOOKS, tstfn(HookEvent.PreDbImport))

    def test_get_applicable_hooks_for_global_un_project_di(self):
        with self.hookconfigs(
            "global_hookconfig_default_unconfigured.json", "project_hookconfig_default_disabled.json"
        ):
            tstfn = self.subject.get_applicable_hooks_for
            self.assertApplHooksEq(GLOB_EN_PROJ_EN_HOOKS, tstfn("custom-glob-en-proj-en"))
            self.assertApplHooksEq(GLOB_DI_PROJ_EN_HOOKS, tstfn("custom-glob-di-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_EN_HOOKS, tstfn("custom-glob-un-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-un"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-un"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-un"))
            self.assertApplHooksEq([], tstfn(HookEvent.GitPreCommit))
            self.assertApplHooksEq([], tstfn(HookEvent.PreStart))
            self.assertApplHooksEq([], tstfn(HookEvent.PreDbImport))

    def test_get_applicable_hooks_for_global_en_project_di(self):
        with self.hookconfigs("global_hookconfig_default_enabled.json", "project_hookconfig_default_disabled.json"):
            tstfn = self.subject.get_applicable_hooks_for
            self.assertApplHooksEq(GLOB_EN_PROJ_EN_HOOKS, tstfn("custom-glob-en-proj-en"))
            self.assertApplHooksEq(GLOB_DI_PROJ_EN_HOOKS, tstfn("custom-glob-di-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_EN_HOOKS, tstfn("custom-glob-un-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-un"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-un"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-un"))
            self.assertApplHooksEq([], tstfn(HookEvent.GitPreCommit))
            self.assertApplHooksEq([], tstfn(HookEvent.PreStart))
            self.assertApplHooksEq([], tstfn(HookEvent.PreDbImport))

    def test_get_applicable_hooks_for_global_di_project_di(self):
        with self.hookconfigs("global_hookconfig_default_disabled.json", "project_hookconfig_default_disabled.json"):
            tstfn = self.subject.get_applicable_hooks_for
            self.assertApplHooksEq(GLOB_EN_PROJ_EN_HOOKS, tstfn("custom-glob-en-proj-en"))
            self.assertApplHooksEq(GLOB_DI_PROJ_EN_HOOKS, tstfn("custom-glob-di-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-di"))
            self.assertApplHooksEq(GLOB_UN_PROJ_EN_HOOKS, tstfn("custom-glob-un-proj-en"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-di"))
            self.assertApplHooksEq([], tstfn("custom-glob-un-proj-un"))
            self.assertApplHooksEq([], tstfn("custom-glob-en-proj-un"))
            self.assertApplHooksEq([], tstfn("custom-glob-di-proj-un"))
            self.assertApplHooksEq([], tstfn(HookEvent.GitPreCommit))
            self.assertApplHooksEq([], tstfn(HookEvent.PreStart))
            self.assertApplHooksEq([], tstfn(HookEvent.PreDbImport))

    @contextmanager
    def hookconfigs(self, global_name, project_name):
        with open(get_fixture_path(FIXTURE_BASE_PATH + global_name), "r") as f:
            self.subject._global_hookconfig = json.load(f)
        with open(get_fixture_path(FIXTURE_BASE_PATH + project_name), "r") as f:
            self.subject._project_hookconfig = json.load(f)
        yield
        self.subject._global_hookconfig = NotImplemented
        self.subject._project_hookconfig = NotImplemented

    def assertPerEventsEqual(
        self,
        expected_per_event: Sequence[ApplicableEventConfiguration],
        result_per_event: Sequence[ApplicableEventConfiguration],
    ):
        for entry in result_per_event:
            for hook_entry in entry["hooks"]:
                hook_entry["hook"] = hook_entry["hook"].to_dict()
        for entry in expected_per_event:
            for hook_entry in entry["hooks"]:
                if isinstance(hook_entry["hook"], Hook):
                    hook_entry["hook"] = hook_entry["hook"].to_dict()

        expected_per_event = sorted(expected_per_event, key=lambda k: HookEvent.key_for(k["event"]))
        result_per_event = sorted(result_per_event, key=lambda k: HookEvent.key_for(k["event"]))
        try:
            self.assertEqual(expected_per_event, result_per_event)
        except AssertionError as err:
            for x in expected_per_event:
                x["event"] = HookEvent.key_for(x["event"])
            for x in result_per_event:
                x["event"] = HookEvent.key_for(x["event"])
            print("Output written to /tmp/riptide_expected.json and /tmp/riptide_actual.json", file=sys.stderr)
            with open("/tmp/riptide_expected.json", "w") as f:
                json.dump(expected_per_event, f, indent=2)
            with open("/tmp/riptide_actual.json", "w") as f:
                json.dump(result_per_event, f, indent=2)

            raise err

    def assertApplHooksEq(
        self, expected: list[LoadedHookConfiguration], actual: Sequence[tuple[bool, str, Hook | AbstractPlugin]]
    ):
        expected_transformed: list[tuple[bool, str, dict | AbstractPlugin]] = []
        for e in expected:
            expected_transformed.append((e["defined_in"] == "project", e["key"], e["hook"].to_dict()))
        actual_transformed: list[tuple[bool, str, dict | AbstractPlugin]] = []
        for a_1, a_2, a_3 in actual:
            if isinstance(a_3, AbstractPlugin):
                actual_transformed.append((a_1, a_2, a_3))
            else:
                actual_transformed.append((a_1, a_2, a_3.to_dict()))

        self.assertEqual(expected_transformed, actual_transformed)
