from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Mapping, Sequence

from riptide.config.document.config import Config
from riptide.engine.abstract import SimpleBindVolume

if TYPE_CHECKING:
    from riptide.hook.manager import HookArgument


class HookHostPathArgument:
    """A host path that should be mounted into the hook command container"""

    __slots__ = ("path", "read_only")

    def __init__(self, path: str, read_only: bool = False):
        self.path = path
        self.read_only = read_only

    def __str__(self):
        return self.path


def apply_hook_mounts(
    config: Config,
    args: Sequence[HookArgument],
    additional_host_mounts: Mapping[str, HookHostPathArgument],  # container path -> host path + ro flag
) -> tuple[Sequence[str], dict[str, SimpleBindVolume]]:
    """Map host paths to virtual container paths and generate bind volume mappings."""
    mounts = dict(additional_host_mounts)
    if "project" in config:
        mounts["/project"] = HookHostPathArgument(config["project"].folder())

    new_args = []
    for arg in args:
        if isinstance(arg, HookHostPathArgument):
            virt_path = f"/riptide/hook/path/{uuid.uuid4()}"
            mounts[virt_path] = arg
            new_args.append(virt_path)
        else:
            new_args.append(arg)

    volumes: dict[str, SimpleBindVolume] = {
        host_path.path: {"bind": container_path, "mode": "ro" if host_path.read_only else "rw"}
        for container_path, host_path in mounts.items()
    }

    return new_args, volumes
