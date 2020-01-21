"""
Implementation for listing and modifying environments when NOT using the dont_sync_named_volumes_with_host
performance option.

Assumes database environments are stored in directories under _riptide/data/<service_name>/env
"""
import os
from typing import TYPE_CHECKING

from riptide.db.impl import AbstractDbEnvImpl

if TYPE_CHECKING:
    from riptide.config.document.service import Service
    from riptide.db.environments import DbEnvironments


class DataDirectoryDbEnvImpl(AbstractDbEnvImpl):
    def list(self):
        """Lists the names of all available database environments."""
        from riptide.db.environments import CONFIG_DBENV__DEFAULT

        dir = os.path.join(self.env.db_service.volume_path(), 'env')
        if not os.path.exists(dir):
            return [CONFIG_DBENV__DEFAULT]

        return next(os.walk(dir))[1]

    def delete(self, name: str):
        """Deletes the target database environment."""
        self.env.engine.path_rm(self._path_to_env(self.env.db_service, name), self.env.project)

    def create(self, name: str):
        """Creates the target database environment."""
        os.makedirs(self._path_to_env(self.env.db_service, name))

    def copy(self, env1: str, env2: str):
        """Copy all data from env1 to env2."""
        new_env_path = self._path_to_env(self.env.db_service, env2)
        old_env_path = self._path_to_env(self.env.db_service, env1)
        self.env.engine.path_copy(old_env_path, new_env_path, self.env.project)

    def exists(self, name: str):
        """Check if the target environment exists."""
        return os.path.exists(self._path_to_env(self.env.db_service, name))

    @classmethod
    def path_for_db_data(cls, db_env: 'DbEnvironments'):
        """
        Path to the current database data directory for the currently active environment.
        If folder does not exist, create.
        """
        path = cls._path_to_env(db_env.db_service, db_env.currently_selected_name())
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def _path_to_env(service: 'Service', env_name: str):
        """Path to the database data directory for environment 'name'."""
        return os.path.join(service.volume_path(), 'env', env_name)
