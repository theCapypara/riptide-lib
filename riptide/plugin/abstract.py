from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from riptide.engine.abstract import AbstractEngine

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
    def after_reload_config(self, config: 'Config'):
        """Called whenever a project is loaded or if the initial configuration is loaded without a project."""

    @abstractmethod
    def get_flag_value(self, config: 'Config', flag_name: str) -> bool:
        """
        Return the value of a requested plugin flag. Return False if not defined.
        The current config is passed, to give a context about the calling project.
        Please note, that flag values are usually loaded before after_reload_config!
        """
