import os

import unittest
from unittest import mock
from unittest.mock import Mock, MagicMock

import riptide.config.document.command as module
from configcrunch.test_utils import YamlConfigDocumentStub
from riptide.config.files import CONTAINER_SRC_PATH
from riptide.tests.stubs import ProjectStub


class CommandTestCase(unittest.TestCase):

    def setUp(self):
        self.fix_with_volumes = module.Command({
            "additional_volumes": [
                {
                    "host": "~/hometest",
                    "container": "/vol1",
                    "mode": "rw"
                },
                {
                    "host": "./reltest1",
                    "container": "/vol2",
                    "mode": "rw"
                },
                {
                    "host": "reltest2",
                    "container": "/vol3",
                    "mode": "rw"
                },
                {
                    "host": "/absolute_with_ro",
                    "container": "/vol4",
                    "mode": "ro"
                },
                {
                    "host": "/absolute_no_mode",
                    "container": "/vol5"
                }
            ]
        })

    def test_header(self):
        cmd = module.Command({})
        self.assertEqual(module.HEADER, cmd.header())

    @unittest.skip("not done yet")
    def test_validate(self):
        """TODO"""

    @mock.patch('riptide.config.document.command.cppath.normalize', return_value='NORMALIZED')
    def test_initialize_data_after_variables(self, normalize_mock: Mock):
        cmd = self.fix_with_volumes
        expected = [
                {
                    "host": "NORMALIZED",
                    "container": "/vol1",
                    "mode": "rw"
                },
                {
                    "host": "NORMALIZED",
                    "container": "/vol2",
                    "mode": "rw"
                },
                {
                    "host": "NORMALIZED",
                    "container": "/vol3",
                    "mode": "rw"
                },
                {
                    "host": "NORMALIZED",
                    "container": "/vol4",
                    "mode": "ro"
                },
                {
                    "host": "NORMALIZED",
                    "container": "/vol5"
                }
        ]
        cmd._initialize_data_after_variables()
        self.assertEqual(5, normalize_mock.call_count, "cppath.normalize has to be called once for each volume")
        self.assertEqual(expected, cmd.doc['additional_volumes'])

    def test_get_project(self):
        cmd = module.Command({})
        project = ProjectStub({}, set_parent_to_self=True)
        cmd.parent_doc = project
        self.assertEqual(project, cmd.get_project())

    def test_get_project_no_parent(self):
        cmd = module.Command({})
        with self.assertRaises(IndexError):
            cmd.get_project()

    @mock.patch("os.path.expanduser", return_value=os.sep + 'HOME')
    def test_collect_volumes(self, expanduser_mock: Mock):
        cmd = self.fix_with_volumes
        expected = {
            # Source code also has to be mounted in:
            ProjectStub.SRC_FOLDER:                         {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'},
            os.path.join(os.sep + 'HOME', 'hometest'):      {'bind': '/vol1', 'mode': 'rw'},
            os.path.join(ProjectStub.FOLDER, './reltest1'): {'bind': '/vol2', 'mode': 'rw'},
            os.path.join(ProjectStub.FOLDER, 'reltest2'):   {'bind': '/vol3', 'mode': 'rw'},
            '/absolute_with_ro':                            {'bind': '/vol4', 'mode': 'ro'},
            '/absolute_no_mode':                            {'bind': '/vol5', 'mode': 'rw'}
        }

        cmd.parent_doc = ProjectStub({}, set_parent_to_self=True)
        self.assertEqual(expected, cmd.collect_volumes())
        # First command had ~ in it:
        expanduser_mock.assert_called_once_with('~')

    def test_resolve_alias_nothing_to_alias(self):
        cmd = module.Command({})
        self.assertEqual(cmd, cmd.resolve_alias())

    def test_resolve_alias_something_to_alias(self):
        # hello world command
        hello_world_command = YamlConfigDocumentStub({'hello': 'world'})
        # The command we want to test
        cmd = module.Command({'aliases': 'hello_world'})
        # The parent app of the command we want to test, that contains both commands
        cmd.parent_doc = YamlConfigDocumentStub({'commands': {
            'hello_world': hello_world_command,
            'our_test': cmd
        }})
        # Make the mocked command's resolve_alias return itself.
        setattr(hello_world_command, 'resolve_alias', MagicMock(return_value=hello_world_command))
        # Assert that we get the hello world command
        self.assertEqual(hello_world_command, cmd.resolve_alias())
        # Make sure resolve_alias was actually called on our mocked command
        hello_world_command.resolve_alias.assert_called_once()

    @mock.patch('os.makedirs')
    @mock.patch('riptide.config.document.command.get_project_meta_folder', return_value='META')
    def test_volume_path(self, meta_folder_mock: Mock, os_makedirs_mock: Mock):
        cmd = module.Command({'$name': 'hello_world'})
        cmd.parent_doc = ProjectStub({}, set_parent_to_self=True)
        expected_path = os.path.join('META', 'cmd_data', 'hello_world')
        self.assertEqual(expected_path, cmd.volume_path())

        meta_folder_mock.assert_called_once_with(ProjectStub.FOLDER)
        os_makedirs_mock.assert_called_once_with(expected_path, exist_ok=True)

    def test_home_path(self):
        cmd = module.Command({})
        self.assertEqual(module.CONTAINER_HOME_PATH, cmd.home_path())
