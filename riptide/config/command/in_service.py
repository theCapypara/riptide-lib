"""Module for functions related to in_service commands"""
from typing import List

from riptide.config.document.app import App
from riptide.config.document.command import Command
from riptide.config.document.project import Project
from riptide.engine.abstract import AbstractEngine


def convert_in_service_to_normal(app: App, command_name: str) -> Command:
    """
    Converts the 'in_service' command identified by `command_name` in `app`
    to a regular command. Image, 'config_from_roles' and additional volumes are based on the
    service that the 'in_service' command was supposed to be run in.
    """
    old_cmd = app['commands'][command_name]
    service = app['services'][old_cmd.get_service(app)]

    env = {}
    env.update(service['environment'] if 'environment' in service else {})
    env.update(old_cmd['environment'] if 'environment' in old_cmd else {})
    new_cmd = Command.from_dict({
        '$name': command_name,
        'image': service['image'],
        'command': old_cmd['command'],
        'additional_volumes': service['additional_volumes'] if 'additional_volumes' in service else {},
        'environment': env,
        'config_from_roles': [old_cmd['in_service_with_role']],
        'use_host_network': old_cmd['use_host_network'] if 'use_host_network' in old_cmd else False
    })
    new_cmd.parent_doc = app
    new_cmd.freeze()
    return new_cmd


def run(engine: AbstractEngine, project: Project, command_name: str, arguments: List[str]) -> int:
    """
    Runs an in_service command.
    If the service for the command is started, command is executed in that service container.
    Otherwise a new container is started.

    Returns exit code of command.
    """
    cmd = project["app"]["commands"][command_name]
    service = cmd.get_service(project["app"])

    if engine.service_status(project, service):
        # Container is running, run in there
        return engine.cmd_in_service(project, command_name, service, arguments)
    else:
        # Container is not running, start a new container
        old_cmd = cmd
        project["app"]["commands"][command_name] = convert_in_service_to_normal(project["app"], command_name)
        ret_code = engine.cmd(project, command_name, arguments)
        project["app"]["commands"][command_name] = old_cmd
        return ret_code
