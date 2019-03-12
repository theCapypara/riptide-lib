"""Generic module to return all sorts of status information for services"""
from typing import Dict, NamedTuple, Union, List

from riptide.config.document.config import Config
from riptide.config.document.project import Project
from riptide.config.service.ports import get_existing_port_mapping
from riptide.engine.abstract import AbstractEngine


class AdditionalPortsEntry(NamedTuple):
    title: str
    host: int
    container: int


class StatusResult(NamedTuple):
    running: bool
    web: Union[str, None]  # proxy url if service has a web port assigned, None otherwise
    additional_ports: List[AdditionalPortsEntry]  # if service has additional ports


def status_for(project: Project, engine: AbstractEngine, system_config: Config) -> Dict[str, StatusResult]:
    """
    Returns the status for a given project's services, including if they are running and
    all their additional ports.
    :param system_config:
    :param engine:
    :param project:
    :return:
    """

    status_dict = {}

    for name, running in engine.status(project, system_config).items():
        service = project["app"]["services"][name]
        if running:
            # Collect URL
            proxy_url = None
            if "port" in service:
                proxy_url = "https://" + service.domain()

            # Collect Additional Ports
            additional_ports = []
            if "additional_ports" in service:
                for entry in service["additional_ports"].values():
                    port_host = get_existing_port_mapping(project, service, entry["host_start"])
                    if port_host:
                        additional_ports.append(AdditionalPortsEntry(
                            title=entry["title"],
                            container=entry["container"],
                            host=port_host
                        ))

            status_dict[name] = StatusResult(
                running=running,
                web=proxy_url,
                additional_ports=additional_ports
            )
        else:
            status_dict[name] = StatusResult(
                running=running,
                web=None,
                additional_ports=[]
            )

    return status_dict
