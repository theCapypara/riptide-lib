from typing import Dict, Union, TYPE_CHECKING

from importlib.metadata import entry_points

from riptide.plugin.abstract import AbstractPlugin

if TYPE_CHECKING:
    pass

PLUGIN_ENTRYPOINT_KEY = "riptide.plugin"
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
        plugins: Dict[str, AbstractPlugin] = {
            entry_point.name: entry_point.load()() for entry_point in entry_points().select(group=PLUGIN_ENTRYPOINT_KEY)
        }

        for name, plugin in plugins.items():
            if not isinstance(plugin, AbstractPlugin):
                raise ValueError(f"The Riptide plugin {name} does not correctly implement AbstractPlugin.")
        loaded_plugins = plugins
    return loaded_plugins
