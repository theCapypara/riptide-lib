"""
Implementation for listing and modifing environments when using the dont_sync_named_volumes_with_host
performance option.

Assumes database environments are stored as named volumes by the engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from riptide.db.impl import AbstractDbEnvImpl

if TYPE_CHECKING:
    from riptide.db.environments import DbEnvironments


class NamedVolumeDbEnvImpl(AbstractDbEnvImpl):
    def list(self):
        """Lists the names of all available database environments."""
        prefix = self.named_volume_prefix_for(self.env)
        assert self.env.engine is not None
        list = [nv[len(prefix) :] for nv in self.env.engine.list_named_volumes() if nv.startswith(prefix)]
        # if the list is empty, still add default.
        if len(list) < 1:
            return ["default"]
        return list

    def delete(self, name: str):
        """Deletes the target database environment."""
        assert self.env.engine is not None
        self.env.engine.delete_named_volume(self.named_volume_for_db_data(self.env, name))

    def exists(self, name: str):
        """Check if the target environment exists."""
        assert self.env.engine is not None
        return self.env.engine.exists_named_volume(self.named_volume_for_db_data(self.env, name))

    def create(self, name: str):
        """Creates the target database environment."""
        assert self.env.engine is not None
        self.env.engine.create_named_volume(self.named_volume_for_db_data(self.env, name))

    def copy(self, env1: str, env2: str):
        """Copy all data from env1 to env2."""
        assert self.env.engine is not None
        self.env.engine.copy_named_volume(
            self.named_volume_for_db_data(self.env, env1),
            self.named_volume_for_db_data(self.env, env2),
        )

    @classmethod
    def named_volume_for_db_data(cls, db_env: DbEnvironments, env_name: str) -> str:
        """Returns the name of the named volume for this database environment"""
        return f"{cls.named_volume_prefix_for(db_env)}{env_name}"

    @staticmethod
    def named_volume_prefix_for(db_env: DbEnvironments) -> str:
        assert db_env.db_service is not None
        driver_name = db_env.db_service["driver"]["name"]
        return f"{db_env.db_service.get_project()['name']}__db_{driver_name}__"
