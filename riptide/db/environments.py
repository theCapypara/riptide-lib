"""Functions for switching the current database environment"""
import json
import os

from riptide.config.files import get_project_meta_folder, remove_all_special_chars
from riptide.db.driver import db_driver_for_service

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

    @staticmethod
    def has_db(project: 'Project'):
        """Returns whether or not this project has a database to manage"""
        return DbEnvironments(project, None).db_service is not None

    @staticmethod
    def path_for_db_data(service: 'Service'):
        """Path to the current database data directory for the currently active environment. If folder does not exist, create."""
        instance = DbEnvironments(service.get_project(), None)
        path = instance._path_to_env(instance.currently_selected_name())
        os.makedirs(path, exist_ok=True)
        return path

    def currently_selected_name(self):
        """Returns the name of the currently selected environment."""
        return self.config['env']

    def list(self):
        """
        Lists all environments
        :return:
        """
        dir = os.path.join(self.db_service.volume_path(), 'env')
        if not os.path.exists(dir):
            return [CONFIG_DBENV__DEFAULT]

        return next(os.walk(dir))[1]

    def switch(self, environment):
        """
        Switch to an already existing environment by name.
        Make sure that the database service is not current running.
        :raises: FileNotFoundError if the database environment doesn't exist yet.
        """
        new_env_path = self._path_to_env(environment)
        if not os.path.exists(new_env_path):
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
        new_env_path = self._path_to_env(environment)
        if os.path.exists(new_env_path):
            raise FileExistsError("Database environment already exists")

        if environment != remove_all_special_chars(environment):
            raise NameError("Invalid name")

        os.makedirs(new_env_path, exist_ok=True)
        if copy_from:
            old_env_path = self._path_to_env(copy_from)
            if not os.path.exists(old_env_path):
                raise FileNotFoundError("Database environment to copy from not found")
            self.engine.path_copy(old_env_path, new_env_path, self.project)

    def drop(self, environment):
        """
        Drop a database envrionment by name
        :raises: FileNotFoundError if the database environment doesn't exist.
        :raises: EnvironmentError if the environment to drop is the one currently in use
        """
        new_env_path = self._path_to_env(environment)
        if self.config[CONFIG_DBENV] == environment:
            raise EnvironmentError("Can not delete currently used environment")
        if not os.path.exists(new_env_path):
            raise FileNotFoundError("Database environment not found")
        self.engine.path_rm(new_env_path, self.project)

    def _path_to_env(self, name):
        """Path to the database data directory for environment 'name'."""
        return os.path.join(self.db_service.volume_path(), 'env', name)

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
