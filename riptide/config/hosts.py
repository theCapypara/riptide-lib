"""Management of hosts-file entries for project services"""
from python_hosts import Hosts, HostsEntry
from python_hosts.exception import UnableToWriteHosts

from riptide.config.document.config import Config


def update_hosts_file(system_config: Config, warning_callback=lambda msg: None):
    """Update the hosts-file for the current project,
    if any is loaded and updating is enabled in configuration.

    The hosts file is written, if it was changed.
    If it can't be written, warning messages are send to the lambda that outputs
    how to manually change the host file.

    :param warning_callback: Callback that receives strings representing warning messages to output to users.
    :param system_config: System configuration
    """

    if system_config["update_hosts_file"]:
        if "project" in system_config:
            hosts = Hosts()
            new_entries = []
            changes = False

            base_url = system_config["proxy"]["url"]
            if not hosts.exists(names=[base_url]):
                changes = True
                new_entries.append(HostsEntry(entry_type='ipv4', address='127.0.0.1', names=[base_url]))

            if "services" in system_config["project"]["app"]:
                for service in system_config["project"]["app"]["services"].values():
                    domain = service.domain()
                    if not hosts.exists(names=[domain]):
                        changes = True
                        new_entries.append(HostsEntry(entry_type='ipv4', address='127.0.0.1', names=[domain]))
            hosts.add(new_entries)
            if changes:
                try:
                    hosts.write()
                except UnableToWriteHosts:
                    warning_callback("Could not update the hosts-file (%s) to configure proxy server routing.\n"
                                     "> Give your user permission to edit this file, to remove this warning.\n"
                                     "> If you wish to manually add the entries instead, "
                                     "add the following entries to %s:\n%s\n"
                                     % (
                                         hosts.hosts_path,
                                         hosts.hosts_path,
                                         "\n".join(["%s\t%s" % (e.address, e.names[0]) for e in new_entries])
                                     ))
