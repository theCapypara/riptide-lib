from collections import OrderedDict

import os

import unittest
from unittest import mock

from unittest.mock import Mock, MagicMock

from schema import SchemaError

import riptide.config.document.command as module
from configcrunch.tests.test_utils import YamlConfigDocumentStub
from riptide.config.files import CONTAINER_SRC_PATH
from riptide.tests.helpers import get_fixture_path
from riptide.tests.stubs import ProjectStub
from riptide.tests.unit.config.service.volumes_test import STUB_PAV__KEY, STUB_PAV__VAL

FIXTURE_BASE_PATH = 'command' + os.sep


class CommandTestCase(unittest.TestCase):

    def setUp(self):
        self.fix_with_volumes = module.Command({
            "additional_volumes": {
                "one": {
                    "host": "~/hometest",
                    "container": "/vol1",
                    "mode": "rw"
                },
                "two": {
                    "host": "./reltest1",
                    "container": "/vol2",
                    "mode": "rw"
                },
                "three": {
                    "host": "reltest2",
                    "container": "/vol3",
                    "mode": "rw"
                },
                "four": {
                    "host": "reltestc",
                    "container": "reltest_container",
                    "mode": "rw"
                },
                "five": {
                    "host": "/absolute_with_ro",
                    "container": "/vol4",
                    "mode": "ro"
                },
                "six": {
                    "host": "/absolute_no_mode",
                    "container": "/vol5"
                }
            }
        })

    def test_header(self):
        cmd = module.Command({})
        self.assertEqual(module.HEADER, cmd.header())

    def test_validate_valids(self):
        valid_names = ['valid_regular.yml', 'valid_alias.yml',
                       'valid_regular_with_some_optionals.yml']
        for name in valid_names:
            with self.subTest(name=name):
                command = module.Command.from_yaml(get_fixture_path(
                    FIXTURE_BASE_PATH + name
                ))
                self.assertTrue(command.validate())

    def test_validate_invalid_alias_no_aliases(self):
        command = module.Command.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_alias_no_aliases.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing keys:"):
            command.validate()

    def test_validate_invalid_regular_no_image(self):
        command = module.Command.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_regular_no_image.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing keys:"):
            command.validate()

    def test_validate_invalid_weird_mixup(self):
        command = module.Command.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_weird_mixup.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Wrong keys"):
            command.validate()

    @mock.patch('riptide.config.document.command.cppath.normalize', return_value='NORMALIZED')
    def test_initialize_data_after_variables(self, normalize_mock: Mock):
        cmd = self.fix_with_volumes
        expected = {
                "one": {
                    "host": "NORMALIZED",
                    "container": "/vol1",
                    "mode": "rw"
                },
                "two": {
                    "host": "NORMALIZED",
                    "container": "/vol2",
                    "mode": "rw"
                },
                "three": {
                    "host": "NORMALIZED",
                    "container": "/vol3",
                    "mode": "rw"
                },
                "four": {
                    "host": "NORMALIZED",
                    "container": "reltest_container",
                    "mode": "rw"
                },
                "five": {
                    "host": "NORMALIZED",
                    "container": "/vol4",
                    "mode": "ro"
                },
                "six": {
                    "host": "NORMALIZED",
                    "container": "/vol5"
                }
        }
        cmd._initialize_data_after_variables()
        self.assertEqual(6, normalize_mock.call_count, "cppath.normalize has to be called once for each volume")
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

    @mock.patch("riptide.config.document.command.process_additional_volumes", return_value={STUB_PAV__KEY: STUB_PAV__VAL})
    def test_collect_volumes(self, process_additional_volumes_mock: Mock):
        cmd = self.fix_with_volumes
        expected = OrderedDict({
            # Source code also has to be mounted in:
            ProjectStub.SRC_FOLDER:                         {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'},
            # process_additional_volumes has to be called
            STUB_PAV__KEY: STUB_PAV__VAL
        })

        cmd.parent_doc = ProjectStub({}, set_parent_to_self=True)
        actual = cmd.collect_volumes()
        self.assertEqual(expected, actual)
        self.assertIsInstance(actual, OrderedDict)

        process_additional_volumes_mock.assert_called_with(
            list(self.fix_with_volumes['additional_volumes'].values()),
            ProjectStub.FOLDER
        )

    @mock.patch("os.get_terminal_size", return_value=(10,20))
    @mock.patch("os.environ.copy", return_value={'ENV': 'VALUE1', 'FROM_ENV': 'has to be overridden'})
    def test_collect_environment(self, *args, **kwargs):
        cmd = module.Command({
            'environment': {
                'FROM_ENV': 'FROM_ENV'
            }
        })
        expected = {
            'ENV': 'VALUE1',
            'FROM_ENV': 'FROM_ENV',
            'COLUMNS': '10',
            'LINES': '20'
        }

        self.assertEqual(expected, cmd.collect_environment())

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
