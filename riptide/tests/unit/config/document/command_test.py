from collections import OrderedDict

import os

import unittest
from unittest import mock

from unittest.mock import Mock, MagicMock, call

from schema import SchemaError

import riptide.config.document.command as module
from configcrunch.tests.test_utils import YamlConfigDocumentStub
from riptide.config.files import CONTAINER_SRC_PATH, CONTAINER_HOME_PATH
from riptide.tests.helpers import get_fixture_path
from riptide.tests.stubs import ProjectStub, process_config_stub
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
            },
            "config_from_roles": ["A", "B"]
        })

    def test_header(self):
        cmd = module.Command({})
        self.assertEqual(module.HEADER, cmd.header())

    def test_validate_valids(self):
        valid_names = ['valid_regular.yml', 'valid_alias.yml',
                       'valid_regular_with_some_optionals.yml',
                       'valid_via_service.yml', 'valid_regular_with_volumes_named.yml']
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
        with self.assertRaises(SchemaError):
            command.validate()

    def test_validate_invalid_regular_no_image(self):
        command = module.Command.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_regular_no_image.yml'
        ))
        with self.assertRaises(SchemaError):
            command.validate()

    def test_validate_invalid_weird_mixup(self):
        command = module.Command.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_weird_mixup.yml'
        ))
        with self.assertRaises(SchemaError):
            command.validate()

    def test_validate_via_service_no_command(self):
        command = module.Command.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_via_service_no_command.yml'
        ))
        with self.assertRaises(SchemaError):
            command.validate()

    def test_get_service_valid(self):
        test_service = YamlConfigDocumentStub({
            'roles': ['rolename']
        })
        app = YamlConfigDocumentStub({
            'services': {
                'test': test_service
            }
        })

        command = module.Command.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'valid_via_service.yml'
        ))
        self.assertEqual('test', command.get_service(app))

    def test_get_service_not_via_service(self):
        test_service = YamlConfigDocumentStub({
            'roles': ['rolename']
        })
        app = YamlConfigDocumentStub({
            'services': {
                'test': test_service
            }
        })

        command = module.Command.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'valid_regular.yml'
        ))
        with self.assertRaisesRegex(TypeError, 'get_service can only be used on "in service" commands.'):
            command.get_service(app)

    def test_get_service_no_service_with_role(self):
        test_service = YamlConfigDocumentStub({
            'roles': []
        })
        app = YamlConfigDocumentStub({
            'services': {
                'test': test_service
            }
        })

        command = module.Command.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'valid_via_service.yml'
        ))
        with self.assertRaisesRegex(ValueError, 'Command .* can not run in service with role rolename: No service with this role found in the app.'):
            command.get_service(app)

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

    @mock.patch("os.environ")
    @mock.patch("riptide.config.document.command.process_additional_volumes", return_value={STUB_PAV__KEY: STUB_PAV__VAL})
    @mock.patch("riptide.config.document.command.process_config", side_effect=process_config_stub)
    def test_collect_volumes(self, process_config_mock: Mock, process_additional_volumes_mock: Mock, os_environ_mock: Mock):
        env = {}
        os_environ_mock.__getitem__.side_effect = env.__getitem__
        os_environ_mock.__iter__.side_effect = env.__iter__
        os_environ_mock.__contains__.side_effect = env.__contains__
        # Fixture also wants config_from_roles A and B
        cmd = self.fix_with_volumes
        # Dict order is not checked here, because it can be arbitrary for config_from_roles. Order
        # is checked in the other collect_volume tests.
        expected = dict({
            # Source code also has to be mounted in:
            ProjectStub.SRC_FOLDER:                         {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'},
            # process_additional_volumes has to be called
            STUB_PAV__KEY: STUB_PAV__VAL,
            # config_from_roles :
            'config1~/FROM_1~serviceRoleA1~False':          {'bind': '/TO_1', 'mode': 'STUB'},
            'config2~/FROM_2~serviceRoleA1~False':          {'bind': '/TO_2', 'mode': 'STUB'},
            'config2~/FROM_2~serviceRoleA2B1~False':        {'bind': '/TO_2', 'mode': 'STUB'},
            'config3~/FROM_3~serviceRoleA2B1~True':         {'bind': '/TO_3', 'mode': 'STUB'},
            'config3~/FROM_3~serviceRoleB2~True':           {'bind': '/TO_3', 'mode': 'STUB'},
        })

        # Config entries
        config1 = {'to': '/TO_1', 'from': '/FROM_1'}
        config2 = {'to': '/TO_2', 'from': '/FROM_2'}
        config3 = {'to': '/TO_3', 'from': '/FROM_3', 'force_recreate': True}

        # Services
        serviceRoleA1 = {
            "__UNIT_TEST_NAME": "serviceRoleA1",
            "roles": ["A"],
            "config": {
                "config1": config1,
                "config2": config2
            }
        }
        # Is in two searched rules, must only be included once:
        serviceRoleA2B1 = {
            "__UNIT_TEST_NAME": "serviceRoleA2B1",
            "roles": ["A", "B"],
            "config": {
                "config2": config2,
                "config3": config3
            }
        }
        serviceRoleB2 = {
            "__UNIT_TEST_NAME": "serviceRoleB2",
            "roles": ["B"],
            "config": {
                "config3": config3
            }
        }
        # Has role C, should not be used:
        serviceRoleC1 = {
            "__UNIT_TEST_NAME": "serviceRoleC1",
            "roles": ["C"],
            "config": {
                "config1": config1,
                "config2": config2
            }
        }

        # The project contains some services matching the defined roles
        cmd.parent_doc = YamlConfigDocumentStub({
            'services': {
                'serviceRoleA1': serviceRoleA1,
                'serviceRoleA2B1': serviceRoleA2B1,
                'serviceRoleB2': serviceRoleB2,
                'serviceRoleC1': serviceRoleC1
            }
        }, parent=ProjectStub({}))

        def get_services_by_role_mock(role):
            if role == "A":
                return [serviceRoleA1, serviceRoleA2B1]
            if role == "B":
                return [serviceRoleA2B1, serviceRoleB2]
            if role == "C":
                return [serviceRoleC1]
            return []

        cmd.parent_doc.get_services_by_role = get_services_by_role_mock
        actual = cmd.collect_volumes()
        self.assertEqual(expected, actual)
        self.assertIsInstance(actual, OrderedDict)

        process_additional_volumes_mock.assert_called_with(
            list(self.fix_with_volumes['additional_volumes'].values()),
            ProjectStub.FOLDER
        )

    @mock.patch("os.environ")
    @mock.patch("riptide.config.document.command.process_additional_volumes", return_value={STUB_PAV__KEY: STUB_PAV__VAL})
    def test_collect_volumes_no_roles(self, process_additional_volumes_mock: Mock, os_environ_mock: Mock):
        env = {}
        os_environ_mock.__getitem__.side_effect = env.__getitem__
        os_environ_mock.__iter__.side_effect = env.__iter__
        os_environ_mock.__contains__.side_effect = env.__contains__
        cmd = self.fix_with_volumes
        expected = OrderedDict({
            # Source code also has to be mounted in:
            ProjectStub.SRC_FOLDER:                         {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'},
            # process_additional_volumes has to be called
            STUB_PAV__KEY: STUB_PAV__VAL
        })

        # The project contains NO services matching the defined roles
        cmd.parent_doc = YamlConfigDocumentStub({"services": {}}, parent=ProjectStub({}))

        def get_services_by_role_mock(role):
            return []

        cmd.parent_doc.get_services_by_role = get_services_by_role_mock
        actual = cmd.collect_volumes()
        self.assertEqual(expected, actual)
        self.assertIsInstance(actual, OrderedDict)

        process_additional_volumes_mock.assert_called_with(
            list(self.fix_with_volumes['additional_volumes'].values()),
            ProjectStub.FOLDER
        )


    @mock.patch("os.environ")
    def test_collect_volumes_ssh_auth_socket(self, os_environ_mock: Mock):
        ssh_auth_path = 'DUMMY'
        env = {'SSH_AUTH_SOCK': ssh_auth_path}
        os_environ_mock.__getitem__.side_effect = env.__getitem__
        os_environ_mock.__iter__.side_effect = env.__iter__
        os_environ_mock.__contains__.side_effect = env.__contains__
        cmd = module.Command({})
        expected = OrderedDict({
            # Source code also has to be mounted in:
            ProjectStub.SRC_FOLDER:                         {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'},
            # SSH_AUTH_SOCK:
            ssh_auth_path:                                  {'bind': ssh_auth_path, 'mode': 'rw'}
        })

        # The project contains NO services matching the defined roles
        cmd.parent_doc = ProjectStub({}, set_parent_to_self=True)
        actual = cmd.collect_volumes()
        self.assertEqual(expected, actual)
        self.assertIsInstance(actual, OrderedDict)

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
        self.assertEqual(CONTAINER_HOME_PATH, cmd.home_path())
