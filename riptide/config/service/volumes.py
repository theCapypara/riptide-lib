"""Logic to process additional volumes data and other volume related functions"""
from collections import OrderedDict

import os
from pathlib import PurePosixPath
from typing import List

from riptide.config.files import CONTAINER_SRC_PATH


def process_additional_volumes(volumes: List[dict], project_folder: str):
    """
    Process the volume entries provided and return volume entries
    as described in :class:`riptide.config.document.service.Service` collect_volumes.
    :returns Map with the volumes
    """
    out = OrderedDict()
    for vol in volumes:
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
        out[vol["host"]] = {'bind': vol["container"], 'mode': mode}
        # Create additional volumes as directories if they don't exist yet
        try:
            os.makedirs(vol["host"], exist_ok=True)
        except FileExistsError:
            pass
    return out
