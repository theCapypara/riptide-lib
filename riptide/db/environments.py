"""Functions for switching the current database environment"""
import json
import os
from typing import TYPE_CHECKING

from riptide.config.files import get_project_meta_folder, remove_all_special_chars
from riptide.db.impl.data_directory import DataDirectoryDbEnvImpl
from riptide.db.impl.named_volume import NamedVolumeDbEnvImpl

if TYPE_CHECKING:
    from riptide.config.document.project import Project
    from riptide.config.document.service import Service

CONFIG_DBENV = 'env'
CONFIG_DBENV__DEFAULT = 'default'

DB_DRIVER_CONFIG_NAME = '.db.json'


class DbEnvironments:
    """Manage database environments for a given project"""

    def __init__(self, project: 'Project', engine: 'AbstractEngine'):
        self.project = project

        # Find and assign db service
        self.db_service = None
        for service in self.project["app"]["services"].values():
            if "db" in service["roles"]:
                self.db_service = service
                break

        self.config = self._read_configuration()
        self.engine = engine

        if project.parent()["performance"]["dont_sync_named_volumes_with_host"]:
            self.impl = NamedVolumeDbEnvImpl(self)
        else:
            self.impl = DataDirectoryDbEnvImpl(self)

    @staticmethod
    def has_db(project: 'Project'):
        """Returns whether or not this project has a database to manage"""
        return DbEnvironments(project, None).db_service is not None

    @staticmethod
    def get_volume_configuration_for_driver(container_bind_path: str, service: 'Service'):
        """
        Returns the volume configuration (collect_volumes format) for use by a DB driver, to collect service volume for data.
        """
        instance = DbEnvironments(service.get_project(), None)
        host_path = DataDirectoryDbEnvImpl.path_for_db_data(instance)
        named_volume = NamedVolumeDbEnvImpl.named_volume_for_db_data(instance, instance.currently_selected_name())
        return {host_path: {
            'bind': container_bind_path,
            'mode': 'rw',
            'name': named_volume
        }}

    def currently_selected_name(self):
        """Returns the name of the currently selected environment."""
        return self.config['env']

    def list(self):
        """
        Lists all environments
        """
        return self.impl.list()

    def switch(self, environment):
        """
        Switch to an already existing environment by name.
        Make sure that the database service is not current running.
        :raises: FileNotFoundError if the database environment doesn't exist yet.
        """
        if not self.impl.exists(environment):
            raise FileNotFoundError("Database environment not found")

        self.config[CONFIG_DBENV] = environment
        self._write_configuration()

    def new(self, environment, copy_from=None):
        """
        Create a new database environment and (optionally) copy from an already existing one
        :raises: FileExistsError if the database environment already exists.
        :raises: FileNotFoundError if the database environment to copy from does not exist.
        :raises:
        """
        if self.impl.exists(environment):
            raise FileNotFoundError("Database environment already exists")

        if environment != remove_all_special_chars(environment):
            raise NameError("Invalid name")

        if copy_from and not self.impl.exists(copy_from):
            raise FileNotFoundError("Database environment to copy from not found")

        self.impl.create(environment)
        if copy_from:
            self.impl.copy(copy_from, environment)

    def drop(self, environment):
        """
        Drop a database envrionment by name
        :raises: FileNotFoundError if the database environment doesn't exist.
        :raises: EnvironmentError if the environment to drop is the one currently in use
        """
        if self.config[CONFIG_DBENV] == environment:
            raise OSError("Can not delete currently used environment")
        if not self.impl.exists(environment):
            raise FileNotFoundError("Database environment not found")

        self.impl.delete(environment)

    def _get_configuration_path(self):
        return os.path.join(get_project_meta_folder(self.project.folder()), DB_DRIVER_CONFIG_NAME)

    def _read_configuration(self):
        path = self._get_configuration_path()
        if not os.path.exists(path):
            # Defaults
            return {
                CONFIG_DBENV: CONFIG_DBENV__DEFAULT
            }
        with open(path, 'r') as fp:
            return json.load(fp)

    def _write_configuration(self):
        with open(self._get_configuration_path(), 'w') as fp:
            return json.dump(self.config, fp)
