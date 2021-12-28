import os

from typing import List, TYPE_CHECKING

from schema import Schema, Optional

from configcrunch import YamlConfigDocument, DocReference, ConfigcrunchError, variable_helper, REMOVE
from riptide.config.document.app import App

HEADER = 'project'

if TYPE_CHECKING:
    from riptide.config.document.config import Config


class Project(YamlConfigDocument):
    """
    A project file. Usually placed as ``riptide.yml`` inside the project directory.
    Has an :class:`riptide.config.document.app.App` in it's ``app`` entry.

    """
    @classmethod
    def header(cls) -> str:
        return HEADER

    @classmethod
    def schema(cls) -> Schema:
        """
        name: str
            Unique name of the project.

        src: str
            Relative path of the source code directory (relative to riptide.yml).
            Services and Commands only get access to this directory.

        app: :class:`~riptide.config.document.app.App`
            App that this project uses.

        [links]: List[str]
            Links to other projects (list of project names).

            Riptide will add all service containers in this project in the TCP/IP networks of all
            projects specified here. This way services in your project can communicate
            with services from other projects and vice-versa.
            If a project in this list does not exist, Riptide will ignore it.

            Please make sure, that service names are not re-used across projects that are linked this way, this could
            lead to unexpected results during service host name resolution.

        [default_services]: List[str]
            List of services to start when running `riptide start`. If not set, all services are started. You can also
            control which services to start using flags. See `riptide start --help` for more information.

        [env_files]: List[str]
            A list of paths to env-files, relative to the project path, that should be read-in by services and command
            when starting. See the ``read_env_file`` flag at :class:`~riptide.config.document.service.Service` and
            :class:`~riptide.config.document.command.Command` for more information.

            Defaults to ["./.env"].

        **Example Document:**

        .. code-block:: yaml

            project:
              name: test-project
              src: src
              app:
                $ref: apps/reference-to-app

        """
        return Schema(
            {
                Optional('$ref'): str,  # reference to other Project documents
                Optional('$path'): str,  # Path to the project file, added by system after loading.
                'name': str,
                'src': str,
                'app': DocReference(App),
                Optional('links'): [str],
                Optional('default_services'): [str],
                Optional('env_files'): [str]
            }
        )

    @classmethod
    def subdocuments(cls):
        return [
            ("app", App)
        ]

    def validate(self) -> bool:
        r = super().validate()
        if '_' in self.internal_get('name'):
            raise ValueError("Project name is invalid: Must not contain underscores (_).")
        return r

    def _initialize_data_after_merge(self, data):
        if 'links' not in data:
            data['links'] = []
        if 'env_files' not in data:
            data['env_files'] = ["./.env"]
        return data

    def folder(self):
        """Returns the project folder if the special internal field "$path" if set or None otherwise"""
        if self.internal_contains("$path"):
            return os.path.dirname(self.internal_get("$path"))
        return None

    def src_folder(self):
        """Returns the absolute path to the folder specified by self['src']. Requires "$path" to be set."""
        if not self.internal_contains("$path"):
            return None
        return os.path.join(self.folder(), self.internal_get("src"))

    def error_str(self) -> str:
        return f"{self.__class__.__name__}<{(self.internal_get('name') if self.internal_contains('name') else '???')}>"

    @variable_helper
    def parent(self) -> 'Config':
        """
        Returns the system configuration document.

        Example usage::

            something: '{{ parent().proxy.url }}'

        Example result::

            something: 'riptide.local'

        """
        # noinspection PyTypeChecker
        return super().parent()
