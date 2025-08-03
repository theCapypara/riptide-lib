"""Module to resolve database drivers for services"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from importlib.metadata import entry_points

from riptide.db.driver.abstract import AbstractDbDriver

if TYPE_CHECKING:
    from riptide.config.document.service import Service


DB_DRIVER_ENTRYPOINT_KEY = "riptide.db_driver"


@overload
def get(service_data: Service) -> AbstractDbDriver | None: ...
@overload
def get(service_data: Service | dict, service: Service) -> AbstractDbDriver | None: ...
def get(service_data: Service | dict, service: Service | None = None) -> AbstractDbDriver | None:
    """Returns the db driver instance for this service, if a driver is defined."""
    # Look up package entrypoints for db drivers
    if service is None:
        from riptide.config.document.service import Service

        assert isinstance(service_data, Service)
        service = service_data

    drivers: dict[str, type[AbstractDbDriver]] = {
        entry_point.name: entry_point.load() for entry_point in entry_points().select(group=DB_DRIVER_ENTRYPOINT_KEY)
    }

    if service_data["driver"]["name"] in drivers:
        return drivers[service_data["driver"]["name"]](service)
    return None
