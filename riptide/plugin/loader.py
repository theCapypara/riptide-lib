import sys
from typing import Dict, Union, TYPE_CHECKING

if sys.version_info < (3, 10):
    import pkg_resources
else:
    from importlib.metadata import entry_points

from riptide.engine.abstract import AbstractEngine
from riptide.plugin.abstract import AbstractPlugin

if TYPE_CHECKING:
    from riptide.config.document.config import Config

PLUGIN_ENTRYPOINT_KEY = 'riptide.plugin'
loaded_plugins: Union[None, Dict[str, AbstractPlugin]] = None


def load_plugins() -> Dict[str, AbstractPlugin]:
    """
    Load the engine by the given name.
    Returns a Dict containing plugin names and interface implementations.

    If they are already loaded, the loaded list is returned.
    """
    global loaded_plugins
    if not loaded_plugins:
        # Look up package entrypoints for engines
        if sys.version_info < (3, 10):
            plugins = {
                entry_point.name:
                    entry_point.load()() for entry_point in pkg_resources.iter_entry_points(PLUGIN_ENTRYPOINT_KEY)
            }
        else:
            plugins = {
                entry_point.name:
                    entry_point.load()() for entry_point in entry_points().select(group=PLUGIN_ENTRYPOINT_KEY)
            }

        for name, plugin in plugins.items():
            if not isinstance(plugin, AbstractPlugin):
                raise ValueError(f"The Riptide plugin {name} does not correctly implement AbstractPlugin.")
        loaded_plugins = plugins
    return loaded_plugins
