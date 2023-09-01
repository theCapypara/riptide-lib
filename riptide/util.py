"""Various utility functions"""
from importlib.metadata import version


class SystemFlag:
    """Useful runtime-dependant global system flags."""
    # Whether or not Riptide is currently run via CLI.
    IS_CLI = 0


def get_riptide_version():
    """Returns the current version of Riptide (lib) as a tuple (major, minor, patch).
    3.0.1 would return (3, 0, 1).
    3.0a1.dev1234 would return (3, "0a1", 'dev1234').
    """
    version = get_riptide_version_raw().split('.')
    major = version[0]
    minor = version[1] if len(version) > 1 else None
    patch = version[2] if len(version) > 2 else None
    try:
        major = int(major)
    except (ValueError, TypeError):
        pass
    try:
        minor = int(minor)
    except (ValueError, TypeError):
        pass
    try:
        patch = int(patch)
    except (ValueError, TypeError):
        pass

    return major, minor, patch


def get_riptide_version_raw():
    return version("riptide-lib")
