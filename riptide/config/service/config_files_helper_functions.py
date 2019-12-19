import os


def read_file(config_file_path: str, file_to_read_in: str) -> str:
    """
    Reads the contents of a file, relative to the configuration file being processed.

    Can not access files in parent directories. Variables in the included file are not processed.

    The parameter ``config_file_path`` is automatically filled by Riptide.

        Example usage::

            {{ read_file('example.txt') }}

        Example result::

            contents of example.txt
    """
    config_file_dir = os.path.realpath(os.path.dirname(config_file_path))
    absolute_file_to_read_in = os.path.realpath(os.path.join(config_file_dir, file_to_read_in))
    is_valid_subpath = absolute_file_to_read_in.startswith(config_file_dir + os.sep)
    if not is_valid_subpath:
        raise ValueError(f"read_file: {file_to_read_in} must be a relative path to the config file {config_file_path} "
                         f"and must not be in a parent directory.")
    if not os.path.exists(absolute_file_to_read_in):
        raise ValueError(f"read_file: File {absolute_file_to_read_in} not found.")

    with open(absolute_file_to_read_in, 'r') as file:
        return file.read().strip()
