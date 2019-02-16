"""
Port mapping logic for additional ports.

Each requested additional_port for each project/service will get a unique
free port starting at it's requested number.

Format of ports.json:
{
  "ports": {
    "1": true  // Taken entries are marked as true. Value does not matter!
  },
  "requests": { // List of requests
    "abc": {  // project
      "cdf": {  // service
        "1": 1 // requested_port: actual taken port
      }
    }
  }
}

TODO: Command to remove port bindings again

"""
import asyncio
import errno
import json
import os
import psutil
import socket

from riptide.config.files import riptide_ports_config_file
from riptide.lib.dict_merge import dict_merge


def _is_open(current_port, list_reserved_ports):
    """
    Check if a port is either reserved by riptide,
    open or reserved by antoher program (TCP only)
    """
    if str(current_port) in list_reserved_ports.keys():
        return False
    try:
        ports = [con.laddr.port for con in psutil.net_connections()]
        return current_port not in ports
    except psutil.AccessDenied:
        # This might fail on some OSes. In this case, try to connect to it.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        # Open ports may refuse connection on Mac. Let's just hope this works :(
        return sock.connect_ex(('127.0.0.1', current_port)) in [0, errno.ECONNREFUSED]


def find_open_port_starting_at(start_port):
    """
    Finds the first free port starting at start_port for the service
    and returns an open port not reserved by riptide or another application
    Used by additional ports logic (get_additional_port), may be used by other system parts.
    """
    port_cfg = PortsConfig.get()
    port_found = False
    current_port = start_port
    while not port_found:
        if _is_open(current_port, port_cfg["ports"]):
            return current_port
        current_port += 1


def get_additional_port(project, service, start_port):
    """
    Finds the first free port starting at start_port for the service
    and returns a unique port binding, not used by any other riptide service
    to use. Looks if a additional port binding exists in for this service, first.
    While assigning, ports that are used by another program (TCP) are also skipped.
    """
    existing = get_existing_port_mapping(project, service, start_port, load=False)
    if existing is not None:
        return existing

    port_cfg = PortsConfig.get()
    port = find_open_port_starting_at(start_port)

    # Port is open, reserve it!
    dict_merge(port_cfg["requests"], {
        project["name"]: {
            service["$name"]: {
                str(start_port): port
            }
        }
    })
    port_cfg["ports"][str(port)] = True


def get_existing_port_mapping(project, service, start_port, load=True):
    if load:
        PortsConfig.load()
    port_cfg = PortsConfig.get()
    if project["name"] in port_cfg["requests"] and \
       service["$name"] in port_cfg["requests"][project["name"]] and \
       str(start_port) in port_cfg["requests"][project["name"]][service["$name"]]:
        # A mapping already exists
        return port_cfg["requests"][project["name"]][service["$name"]][str(start_port)]
    return None


class PortsConfig:
    ports_config = None

    @classmethod
    def load(cls):
        cls.ports_config = {"ports": {}, "requests": {}}
        if os.path.exists(riptide_ports_config_file()):
            with open(riptide_ports_config_file(), mode='r') as file:
                cls.ports_config = json.load(file)

    @classmethod
    def get(cls):
        return cls.ports_config

    @classmethod
    def write(cls):
        with open(riptide_ports_config_file(), mode='w') as file:
            json.dump(cls.ports_config, file)
