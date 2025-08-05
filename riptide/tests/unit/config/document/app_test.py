import os
import unittest
from unittest import mock

from schema import SchemaError

import riptide.config.document.app as module

from riptide.tests.configcrunch_test_utils import YamlConfigDocumentStub
from riptide.tests.helpers import get_fixture_path

FIXTURE_BASE_PATH = "app" + os.sep


class AppTestCase(unittest.TestCase):
    def test_header(self):
        app = module.App.from_dict({})
        self.assertEqual(module.HEADER, app.header())

    def test_validate_valids(self):
        valid_names = ["valid.yml", "integration_app.yml"]
        for name in valid_names:
            with self.subTest(name=name):
                app = module.App.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + name))
                self.assertTrue(app.validate())

    def test_validate_valid_with_some_optionals(self):
        app = module.App.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "valid_with_some_optionals.yml"))
        self.assertTrue(app.validate())

    def test_validate_invalid_no_name(self):
        app = module.App.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_no_name.yml"))
        with self.assertRaisesRegex(SchemaError, "Missing key: 'name'"):
            app.validate()

    @mock.patch("riptide.config.document.app.YamlConfigDocument.resolve_and_merge_references")
    def test_resolve_and_merge_references_no_subdocs(self, super_mock):
        doc = {"name": "test"}
        app = module.App(doc)
        app.resolve_and_merge_references(["./path1", "./path2"])
        super_mock.assert_called_once_with(["./path1", "./path2"])

    @unittest.skip("Needs to be rewritten for configcrunch 1.0+")
    def test_resolve_and_merge_references_with_services(self):
        raise NotImplementedError()  # see git history for previous implementation & rewriting

    @unittest.skip("Needs to be rewritten for configcrunch 1.0+")
    def test_resolve_and_merge_references_with_services_no_dict(self):
        raise NotImplementedError()  # see git history for previous implementation & rewriting

    @unittest.skip("Needs to be rewritten for configcrunch 1.0+")
    def test_resolve_and_merge_references_with_commands(self):
        raise NotImplementedError()  # see git history for previous implementation & rewriting

    @unittest.skip("Needs to be rewritten for configcrunch 1.0+")
    def test_resolve_and_merge_references_with_commands_no_dict(self):
        raise NotImplementedError()  # see git history for previous implementation & rewriting

    def test_get_service_by_role(self):
        SEARCHED_ROLE = "needle"

        service_no_roles = {"$name": "service1"}

        service_not_searched_role = {"$name": "service1", "roles": ["role1", "role2", "role3"]}

        service_searched_role = {"$name": "service1", "roles": ["role1", SEARCHED_ROLE, "role2", "role3"]}

        doc = {
            "name": "test",
            "services": {
                "service_no_roles": YamlConfigDocumentStub(service_no_roles),
                "service_not_searched_role": YamlConfigDocumentStub(service_not_searched_role),
                "service_searched_role": YamlConfigDocumentStub(service_searched_role),
            },
        }

        app = module.App(doc)

        result = app.get_service_by_role(SEARCHED_ROLE)
        result.freeze()
        self.assertEqual(service_searched_role, result.doc)

    def test_get_services_by_role(self):
        SEARCHED_ROLE = "needle"

        service_no_roles = {"$name": "service1"}

        service_searched_role1 = {"$name": "service1", "roles": ["role1", SEARCHED_ROLE, "role2", "role3"]}

        service_searched_role2 = {"$name": "service2", "roles": ["role1", SEARCHED_ROLE, "role2", "role3"]}

        doc = {
            "name": "test",
            "services": {
                "service_no_roles": YamlConfigDocumentStub(service_no_roles),
                "service_searched_role1": YamlConfigDocumentStub(service_searched_role1),
                "service_searched_role2": YamlConfigDocumentStub(service_searched_role2),
            },
        }

        app = module.App(doc)

        result = app.get_services_by_role(SEARCHED_ROLE)
        self.assertEqual(2, len(result))
        result[0].freeze()
        self.assertIn(result[0].doc, [service_searched_role1, service_searched_role2])
        result[1].freeze()
        self.assertIn(result[1].doc, [service_searched_role1, service_searched_role2])
