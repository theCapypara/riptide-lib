"""Module to resolve database drivers for services"""
from typing import Union, TYPE_CHECKING, Optional

import pkg_resources

from riptide.db.driver.abstract import AbstractDbDriver
if TYPE_CHECKING:
    from riptide.config.document.service import Service


DB_DRIVER_ENTRYPOINT_KEY = 'riptide.db_driver'


def get(service_data: Union['Service', dict], service: Optional['Service'] = None) -> Union[AbstractDbDriver, None]:
    """Returns the db driver instance for this service, if a driver is defined."""
    # Look up package entrypoints for db drivers
    if service is None:
        service = service_data
    drivers = {
        entry_point.name:
            entry_point.load() for entry_point in pkg_resources.iter_entry_points(DB_DRIVER_ENTRYPOINT_KEY)
    }

    if service_data["driver"]["name"] in drivers:
        return drivers[service_data["driver"]["name"]](service)
    return None
