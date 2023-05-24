import os
import unittest
from unittest import mock
from unittest.mock import call

from schema import SchemaError

import riptide.config.document.app as module
from configcrunch import ConfigcrunchError

from riptide.tests.configcrunch_test_utils import YamlConfigDocumentStub
from riptide.tests.helpers import get_fixture_path

FIXTURE_BASE_PATH = 'app' + os.sep


class AppTestCase(unittest.TestCase):

    def test_header(self):
        app = module.App.from_dict({})
        self.assertEqual(module.HEADER, app.header())

    def test_validate_valids(self):
        valid_names = ['valid.yml', 'integration_app.yml']
        for name in valid_names:
            with self.subTest(name=name):
                app = module.App.from_yaml(get_fixture_path(
                    FIXTURE_BASE_PATH + name
                ))
                self.assertTrue(app.validate())

    def test_validate_valid_with_some_optionals(self):
        app = module.App.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'valid_with_some_optionals.yml'
        ))
        self.assertTrue(app.validate())

    def test_validate_invalid_no_name(self):
        app = module.App.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_no_name.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing key: 'name'"):
            app.validate()

    @mock.patch("riptide.config.document.app.YamlConfigDocument.resolve_and_merge_references")
    def test_resolve_and_merge_references_no_subdocs(self, super_mock):
        doc = {
            'name': 'test'
        }
        app = module.App(doc)
        app.resolve_and_merge_references(['./path1', './path2'])
        super_mock.assert_called_once_with(['./path1', './path2'])

    @unittest.skip("Needs to be rewritten for configcrunch 1.0+")
    def test_resolve_and_merge_references_with_services(self):
        paths = ['path1', 'path2']

        service1 = {'key1': 'value1'}
        service2 = {'key2': 'value2'}
        doc = {
            'name': 'test',
            'services': {
                'service1': service1,
                'service2': service2
            }
        }

        with mock.patch(
                "riptide.config.document.app.load_subdocument",
                side_effect=side_effect_for_load_subdocument()
        ) as load_subdoc_mock:
            app = module.App(doc)
            app.resolve_and_merge_references(paths)

            self.assertIsInstance(app['services']['service1'], YamlConfigDocumentStub)
            self.assertIsInstance(app['services']['service2'], YamlConfigDocumentStub)
            self.assertEqual({'$name': 'service1', 'key1': 'value1'}, app['services']['service1'].doc)
            self.assertEqual({'$name': 'service2', 'key2': 'value2'}, app['services']['service2'].doc)

            load_subdoc_mock.assert_has_calls([
                call(service1, app, module.Service, paths),
                call(service2, app, module.Service, paths)
            ], any_order=True)

    @unittest.skip("Needs to be rewritten for configcrunch 1.0+")
    def test_resolve_and_merge_references_with_services_no_dict(self):

        paths = ['path1', 'path2']

        service1 = 'nodict'
        doc = {
            'name': 'test',
            'services': {
                'service1': service1,
            }
        }

        with mock.patch(
                "riptide.config.document.app.load_subdocument",
                side_effect=side_effect_for_load_subdocument()
        ):
            app = module.App(doc)
            with self.assertRaises(ConfigcrunchError):
                app.resolve_and_merge_references(paths)

    @unittest.skip("Needs to be rewritten for configcrunch 1.0+")
    def test_resolve_and_merge_references_with_commands(self):
        paths = ['path1', 'path2']

        cmd1 = {'key1': 'value1'}
        cmd2 = {'key2': 'value2'}
        doc = {
            'name': 'test',
            'commands': {
                'cmd1': cmd1,
                'cmd2': cmd2
            }
        }

        with mock.patch(
                "riptide.config.document.app.load_subdocument",
                side_effect=side_effect_for_load_subdocument()
        ) as load_subdoc_mock:
            app = module.App(doc)
            app.resolve_and_merge_references(paths)

            self.assertIsInstance(app['commands']['cmd1'], YamlConfigDocumentStub)
            self.assertIsInstance(app['commands']['cmd2'], YamlConfigDocumentStub)
            self.assertEqual({'$name': 'cmd1', 'key1': 'value1'}, app['commands']['cmd1'].doc)
            self.assertEqual({'$name': 'cmd2', 'key2': 'value2'}, app['commands']['cmd2'].doc)

            load_subdoc_mock.assert_has_calls([
                call(cmd1, app, module.Command, paths),
                call(cmd2, app, module.Command, paths)
            ], any_order=True)

    @unittest.skip("Needs to be rewritten for configcrunch 1.0+")
    def test_resolve_and_merge_references_with_commands_no_dict(self):

        paths = ['path1', 'path2']

        cmd1 = 'nodict'
        doc = {
            'name': 'test',
            'commands': {
                'cmd1': cmd1,
            }
        }

        with mock.patch(
                "riptide.config.document.app.load_subdocument",
                side_effect=side_effect_for_load_subdocument()
        ):
            app = module.App(doc)
            with self.assertRaises(ConfigcrunchError):
                app.resolve_and_merge_references(paths)

    def test_get_service_by_role(self):

        SEARCHED_ROLE = 'needle'

        service_no_roles = {
            '$name': 'service1'
        }

        service_not_searched_role = {
            '$name': 'service1',
            'roles': [
                'role1', 'role2', 'role3'
            ]
        }

        service_searched_role = {
            '$name': 'service1',
            'roles': [
                'role1', SEARCHED_ROLE, 'role2', 'role3'
            ]
        }

        doc = {
            'name': 'test',
            'services': {
                'service_no_roles': YamlConfigDocumentStub(service_no_roles),
                'service_not_searched_role': YamlConfigDocumentStub(service_not_searched_role),
                'service_searched_role': YamlConfigDocumentStub(service_searched_role)
            }
        }

        app = module.App(doc)

        result = app.get_service_by_role(SEARCHED_ROLE)
        result.freeze()
        self.assertEqual(service_searched_role, result.doc)

    def test_get_services_by_role(self):

        SEARCHED_ROLE = 'needle'

        service_no_roles = {
            '$name': 'service1'
        }

        service_searched_role1 = {
            '$name': 'service1',
            'roles': [
                'role1', SEARCHED_ROLE, 'role2', 'role3'
            ]
        }

        service_searched_role2 = {
            '$name': 'service2',
            'roles': [
                'role1', SEARCHED_ROLE, 'role2', 'role3'
            ]
        }

        doc = {
            'name': 'test',
            'services': {
                'service_no_roles': YamlConfigDocumentStub(service_no_roles),
                'service_searched_role1': YamlConfigDocumentStub(service_searched_role1),
                'service_searched_role2': YamlConfigDocumentStub(service_searched_role2)
            }
        }

        app = module.App(doc)

        result = app.get_services_by_role(SEARCHED_ROLE)
        self.assertEqual(2, len(result))
        result[0].freeze()
        self.assertIn(result[0].doc, [service_searched_role1, service_searched_role2])
        result[1].freeze()
        self.assertIn(result[1].doc, [service_searched_role1, service_searched_role2])
