"""Module to resolve database drivers for services"""
from typing import Union

import pkg_resources

from riptide.db.driver.abstract import AbstractDbDriver


DB_DRIVER_ENTRYPOINT_KEY = 'riptide.db_driver'


def get(service: 'Service') -> Union[AbstractDbDriver, None]:
    """Returns the db driver instance for this service, if a driver is defined."""
    # Look up package entrypoints for db drivers
    drivers = {
        entry_point.name:
            entry_point.load() for entry_point in pkg_resources.iter_entry_points(DB_DRIVER_ENTRYPOINT_KEY)
    }

    if service["driver"]["name"] in drivers:
        return drivers[service["driver"]["name"]](service)
    return None
