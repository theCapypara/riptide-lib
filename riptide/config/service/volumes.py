"""Logic to process additional volumes data and other volume related functions"""

import os
import platform
from collections import OrderedDict
from pathlib import PurePosixPath
from stat import S_ISDIR

from riptide.config.files import CONTAINER_SRC_PATH

VOLUME_TYPE_DIRECTORY = "directory"
VOLUME_TYPE_FILE = "file"


def process_additional_volumes(volumes: list[dict], project_folder: str):
    """
    Process the volume entries provided and return volume entries
    as described in :class:`riptide.config.document.service.Service` collect_volumes.
    :returns Map with the volumes
    """
    out = OrderedDict()
    for vol in volumes:
        # Skip volumes that are not marked for this platform (if host_system is defined as a filter)
        if "host_system" in vol:
            if vol["host_system"] != platform.system():
                continue
        # ~ paths
        if vol["host"][0] == "~":
            vol["host"] = os.path.expanduser("~") + vol["host"][1:]
        # Relative paths
        if not os.path.isabs(vol["host"]):
            vol["host"] = os.path.join(project_folder, vol["host"])

        # relative container paths
        if not PurePosixPath(vol["container"]).is_absolute():
            vol["container"] = str(PurePosixPath(CONTAINER_SRC_PATH).joinpath(vol["container"]))

        mode = vol["mode"] if "mode" in vol else "rw"
        out[vol["host"]] = {"bind": vol["container"], "mode": mode}

        # Create additional volumes as defined type, if not exist
        has_type_defined = "type" in vol
        stat_is_dir = True
        vol_type = vol["type"] if has_type_defined else VOLUME_TYPE_DIRECTORY
        try:
            stat = os.lstat(vol["host"])
            stat_is_dir = S_ISDIR(stat.st_mode)
            if stat_is_dir:
                if vol_type == VOLUME_TYPE_FILE:
                    raise IsADirectoryError(
                        f"The file at `{vol['host']}` is a directory, but the volume is defined as a regular file."
                    )
            elif has_type_defined and vol_type == VOLUME_TYPE_DIRECTORY:
                raise NotADirectoryError(
                    f"The file at `{vol['host']}` is a regular file, but the volume is defined as a directory."
                )

        except FileNotFoundError:
            if vol_type == VOLUME_TYPE_FILE:
                # Create as file
                os.makedirs(os.path.dirname(vol["host"]), exist_ok=True)
                open(vol["host"], "a").close()
            else:
                # Create as dir
                os.makedirs(vol["host"], exist_ok=True)

        # If volume_name is specified, add it to the volume definition
        if "volume_name" in vol:
            # Prevent the user from accidentally defining a named volume for something where the host path is a file,
            # because named volumes can not be files.
            if vol_type == VOLUME_TYPE_FILE or not stat_is_dir:
                raise NotADirectoryError(
                    f"The `volume_name` option can only be used for directory paths. `{vol['host']}` is not a directory."
                )
            out[vol["host"]]["name"] = vol["volume_name"]
    return out
