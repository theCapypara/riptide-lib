from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from riptide.db.environments import DbEnvironments


class AbstractDbEnvImpl(ABC):
    def __init__(self, db_env: 'DbEnvironments'):
        self.env = db_env

    @abstractmethod
    def list(self):
        """Lists the names of all available database environments."""

    @abstractmethod
    def delete(self, name: str):
        """Deletes the target database environment."""

    @abstractmethod
    def exists(self, name: str):
        """Check if the target environment exists."""

    @abstractmethod
    def create(self, name: str):
        """Creates the target database environment."""

    @abstractmethod
    def copy(self, env1: str, env2: str):
        """Copy all data from env1 to env2."""
