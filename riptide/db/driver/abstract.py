from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, TYPE_CHECKING

from riptide.engine.abstract import AbstractEngine

if TYPE_CHECKING:
    from riptide.config.document.service import Service


class DbValidationError(Exception):
    pass


class DbImportExport(Exception):
    pass


class AbstractDbDriver(ABC):
    def __init__(self, service: Service):
        self.service = service

    @abstractmethod
    def validate_service(self) -> bool:
        """
        Validate custom constraints the services must met to use this driver.
        May return true or throw DbValidationError.
        """
        pass

    @abstractmethod
    def importt(self, engine: AbstractEngine, absolute_path_to_import_object):
        """Import a directory/file into the database."""
        pass

    @abstractmethod
    def export(self, engine: AbstractEngine, absolute_path_to_export_target):
        """Export a directory/file representing the database data from the database. Must be importable with importt."""
        pass

    @abstractmethod
    def collect_volumes(self):
        """Return volumes to add for services with this db driver. For format :see: Service.collect_volumes"""
        pass

    @abstractmethod
    def collect_additional_ports(self):
        """
        Return additional port mappings to add for services with this db driver.
        Format is the same has Service Documents 'additional_ports' object. See schema of Service.
        """
        pass

    @abstractmethod
    def collect_environment(self):
        """
        Return environment variables to pass to service containers
        For format :see: Service.collect_environment
        """
        pass

    @abstractmethod
    def ask_for_import_file(self):
        """
        Return a prompt to show the user in an CLI/GUI that prompts them to enter
        the path to the import file/directory.
        :return:
        """

    @abstractmethod
    def collect_info(self) -> Dict[str, str]:
        """
        Collect information about accessing the database.

        Returned dict is a map of descriptions.
        """
        pass
