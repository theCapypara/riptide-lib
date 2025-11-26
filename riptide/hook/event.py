from __future__ import annotations

from enum import Enum
from typing import Any, Sequence, TypeAlias, TypeGuard

CUSTOM_HOOK_EVENT_PREFIX = "custom-"


class HookEvent(Enum):
    """
    An event that triggers hooks.

    In addition to events listed, custom events can be used with the prefix ``custom-``, these
    can be triggered by ``riptide hook-trigger``.
    """

    PreStart = "pre-start"
    """
    Hook is run before Riptide starts services when using ``riptide start`` or ``riptide restart``.
    
    .. warning:: Hooks are NOT executed if the Proxy Server starts a project. 
                 Please consider the ``pre_start`` attribute of services 
                 for important pre-start commands. ``riptide start-fg`` does not trigger this event
                 for interactive services.
                 
    Parameters:

    - Comma-seperated list of names that are about to be started
    """

    PostStart = "post-start"
    """
    Hook is run after Riptide started services when using ``riptide start`` or ``riptide restart``.
    
    .. warning:: Hooks are NOT executed if the Proxy Server starts a project. 
                 Please consider the ``post_start`` attribute of services 
                 for important post-start commands. ``riptide start-fg`` does not trigger this event
                 for interactive services.
                 
    Parameters:

    - Comma-seperated list of names that were requested to be started and are now started
    """

    PreStop = "pre-stop"
    """
    Hook is run before Riptide stops services when using ``riptide stop`` or ``riptide restart``.
    
    .. warning:: Hooks are NOT executed if the Proxy Server stops a project.
                 
    Parameters:

    - Comma-seperated list of names that are about to be stopped
    """

    PostStop = "post-stop"
    """
    Hook is run after Riptide stopped services when using ``riptide stop`` or ``riptide restart`` (or another
    command that switched the environment).
    
    .. warning:: Hooks are NOT executed if the Proxy Server stops a project.
                 
    Parameters:
    
    - Comma-seperated list of names that are now stopped (including services that were already stopped)
    """

    PreDbSwitch = "pre-db-switch"
    """
    Hook is run before Riptide switches database environments when using ``riptide db-switch`` (or another
    command that switched the environment).
                 
    Parameters:

    - Currently active database environment name
    - Database environment name requested to switch to
    """

    PostDbSwitch = "post-db-switch"
    """
    Hook is run before Riptide switches database environments when using ``riptide db-switch``.
                 
    Parameters:

    - Name of database environment that was switched to
    """

    PreDbNew = "pre-db-new"
    """
    Hook is run before Riptide created a new blank database environment when using ``riptide db-new``.
                 
    Parameters:

    - Name of database environment that is about to be created
    """

    PostDbNew = "post-db-new"
    """
    Hook is run after Riptide created a new blank database environment when using ``riptide db-new``, but before
    Riptide has switched to this new environment.
                 
    Parameters:

    - Name of database environment that was created
    """

    PreDbImport = "pre-db-import"
    """
    Hook is run before Riptide imports a file into a database environment when using ``riptide db-import``
    or ``riptide setup``.
                 
    Parameters:
    
    - Currently active database environment name
    - Path to the file to import (for hook commands this file is mounted)
    """

    PostDbImport = "post-db-import"
    """
    Hook is run after Riptide imported a file into a database environment when using ``riptide db-import``.
                 
    Parameters:

    - Currently active database environment name
    - Path to the imported file (for hook commands this file is mounted)
    """

    PreDbExport = "pre-db-export"
    """
    Hook is run before Riptide exports a file from a database environment when using ``riptide db-export``.
                 
    Parameters:

    - Database environment name
    """

    PostDbExport = "post-db-export"
    """
    Hook is run after Riptide exported a file from a database environment when using ``riptide db-export``.
                 
    Parameters:

    - Database environment name
    - Path to the file that contains the exported data (for hook commands this file is mounted)
    """

    PreDbCopy = "pre-db-copy"
    """
    Hook is run before Riptide copied a database environment when using ``riptide db-copy``.
                 
    Parameters:

    - Name of database environment that is being copied from
    - Name of database environment that is being copied to
    """

    PostDbCopy = "post-db-copy"
    """
    Hook is run after Riptide copied a database environment when using ``riptide db-new``, but before
    Riptide has switched to this new environment.
                 
    Parameters:

    - Name of database environment that was being copied from
    - Name of database environment that was being copied to
    """

    PreFileImport = "pre-file-import"
    """
    Hook is run before Riptide imports a file into the project when using ``riptide import-files``.
                 
    Parameters:

    - Key of the import definition
    - Path to the file to import (for hook commands this file is mounted)
    """

    PostFileImport = "post-file-import"
    """
    Hook is run after Riptide imported a file into the project when using ``riptide import-files``
    or ``riptide setup``.
                 
    Parameters:

    - Key of the import definition
    - Path to the imported file (for hook commands this file is mounted)
    """

    PostUpdate = "post-update"
    """
    Hook is run after Riptide processed image and repo updates when using ``riptide update``.
                 
    Parameters: none
    """

    PostSetup = "post-setup"
    """
    Hook is run at the end of the interactive setup wizard when using ``riptide setup``.
                 
    Parameters:
    
    - ``new-project`` if the wizard was run in "new project" mode, ``existing-project`` otherwise
    """

    GitApplypatchMsg = "git-applypatch-msg"
    """
    Hook is run when Git triggers a ``applypatch-msg`` Git Hook. Riptide forwards all arguments and environment
    variables that Git provides to the hook.
    See `documentation <https://git-scm.com/docs/githooks>`_.
    """

    GitPreApplypatch = "git-pre-applypatch"
    """
    Hook is run when Git triggers a ``pre-applypatch`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitPostApplypatch = "git-post-applypatch"
    """
    Hook is run when Git triggers a ``post-applypatch`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitCommitMsg = "git-commit-msg"
    """
    Hook is run when Git triggers a ``commit-msg`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitPreCommit = "git-pre-commit"
    """
    Hook is run when Git triggers a ``pre-commit`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitPostCommit = "git-post-commit"
    """
    Hook is run when Git triggers a ``post-commit`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitPrepareCommitMsg = "git-prepare-commit-msg"
    """
    Hook is run when Git triggers a ``prepare-commit-msg`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitPostCheckout = "git-post-checkout"
    """
    Hook is run when Git triggers a ``post-checkout`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitPreRebase = "git-pre-rebase"
    """
    Hook is run when Git triggers a ``pre-rebase`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitPreAutoGc = "git-pre-auto-gc"
    """
    Hook is run when Git triggers a ``pre-auto-gc`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitPrePush = "git-pre-push"
    """
    Hook is run when Git triggers a ``pre-push`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitPostRewrite = "git-post-rewrite"
    """
    Hook is run when Git triggers a ``post-rewrite`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    GitPostMerge = "git-post-merge"
    """
    Hook is run when Git triggers a ``post-merge`` Git Hook.
    See documentation of `git-applypatch-msg` for more information.
    """

    key: str

    def __init__(self, key: str):
        self.key = key

    @classmethod
    def try_from_key(cls, key: str) -> HookEvent | None:
        match key:
            case "pre-start":
                return cls.PreStart
            case "post-start":
                return cls.PostStart
            case "pre-stop":
                return cls.PreStop
            case "post-stop":
                return cls.PostStop
            case "pre-db-switch":
                return cls.PreDbSwitch
            case "post-db-switch":
                return cls.PostDbSwitch
            case "pre-db-new":
                return cls.PreDbNew
            case "post-db-new":
                return cls.PostDbNew
            case "pre-db-import":
                return cls.PreDbImport
            case "post-db-import":
                return cls.PostDbImport
            case "pre-db-export":
                return cls.PreDbExport
            case "post-db-export":
                return cls.PostDbExport
            case "pre-db-copy":
                return cls.PreDbCopy
            case "post-db-copy":
                return cls.PostDbCopy
            case "pre-file-import":
                return cls.PreFileImport
            case "post-file-import":
                return cls.PostFileImport
            case "post-update":
                return cls.PostUpdate
            case "post-setup":
                return cls.PostSetup
            case "git-pre-commit":
                return cls.GitPreCommit
            case "git-prepare-commit-msg":
                return cls.GitPrepareCommitMsg
            case "git-commit-msg":
                return cls.GitCommitMsg
            case "git-post-commit":
                return cls.GitPostCommit
            case "git-applypatch-msg":
                return cls.GitApplypatchMsg
            case "git-pre-applypatch":
                return cls.GitPreApplypatch
            case "git-post-applypatch":
                return cls.GitPostApplypatch
            case "git-pre-rebase":
                return cls.GitPreRebase
            case "git-post-rewrite":
                return cls.GitPostRewrite
            case "git-post-checkout":
                return cls.GitPostCheckout
            case "git-post-merge":
                return cls.GitPostMerge
            case "git-pre-push":
                return cls.GitPrePush
            case "git-pre-auto-gc":
                return cls.GitPreAutoGc
        return None

    @classmethod
    def try_any_from_key(cls, key: str) -> AnyHookEvent | None:
        if key.startswith(CUSTOM_HOOK_EVENT_PREFIX):
            return key
        return cls.try_from_key(key)

    @classmethod
    def git_events(cls) -> Sequence[HookEvent]:
        return [
            cls.GitPreCommit,
            cls.GitPrepareCommitMsg,
            cls.GitCommitMsg,
            cls.GitPostCommit,
            cls.GitApplypatchMsg,
            cls.GitPreApplypatch,
            cls.GitPostApplypatch,
            cls.GitPreRebase,
            cls.GitPostRewrite,
            cls.GitPostCheckout,
            cls.GitPostMerge,
            cls.GitPrePush,
            cls.GitPreAutoGc,
        ]

    @staticmethod
    def validate(event: Any) -> AnyHookEvent | None:
        """
        Checks that a hook event is known (or custom),
        returns the corresponding hook enum or custom event string, if valid.
        """
        if isinstance(event, HookEvent):
            return event
        if isinstance(event, str):
            candidate = HookEvent.try_any_from_key(event)
            if candidate:
                return candidate
        return None

    @staticmethod
    def is_custom(event: AnyHookEvent) -> TypeGuard[str]:
        return isinstance(event, str)

    @staticmethod
    def key_for(event: AnyHookEvent) -> str:
        if isinstance(event, HookEvent):
            return event.key
        return event


AnyHookEvent: TypeAlias = HookEvent | str
"""A known hook event or a string starting with ``custom-``. Can be validated with ``HookEvent.validate``."""
