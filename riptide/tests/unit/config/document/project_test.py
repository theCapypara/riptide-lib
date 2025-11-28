import os
import unittest
from unittest import mock
from unittest.mock import Mock

import riptide.config.document.project as module
from configcrunch import YamlConfigDocument
from riptide.tests.helpers import get_fixture_path
from schema import SchemaError

FIXTURE_BASE_PATH = "project" + os.sep


class ProjectTestCase(unittest.TestCase):
    def test_header(self):
        cmd = module.Project.from_dict({})
        self.assertEqual(module.HEADER, cmd.header())

    def test_validate_valids(self):
        valid_names = ["valid.yml", "integration_all.yml", "integration_no_command.yml", "integration_no_service.yml"]
        for name in valid_names:
            with self.subTest(name=name):
                project = module.Project.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + name))
                self.assertTrue(project.validate())

    def test_validate_invalid_no_app(self):
        project = module.Project.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_no_app.yml"))
        with self.assertRaisesRegex(SchemaError, "Missing key: 'app'"):
            project.validate()

    def test_validate_invalid_no_name(self):
        project = module.Project.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_no_name.yml"))
        with self.assertRaisesRegex(SchemaError, "Missing key: 'name'"):
            project.validate()

    def test_validate_invalid_no_src(self):
        project = module.Project.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_no_src.yml"))
        with self.assertRaisesRegex(SchemaError, "Missing key: 'src'"):
            project.validate()

    @mock.patch("riptide.config.document.project.Project.resolve_and_merge_references")
    def test_resolve_and_merge_references_no_subdocs(self, super_mock):
        doc = {"name": "test"}
        project = module.Project(doc)
        project.resolve_and_merge_references(["./path1", "./path2"])
        super_mock.assert_called_once_with(["./path1", "./path2"])

    def test_resolve_and_merge_references_with_app(self):
        paths = ["path1", "path2"]

        app = {"key1": "value1"}
        doc = {"name": "test", "app": app}

        project = module.Project(doc)
        project.resolve_and_merge_references(paths)
        project.freeze()

        self.assertIsInstance(project["app"], YamlConfigDocument)
        self.assertEqual(app, project["app"].doc)

    def test_resolve_and_merge_references_with_app_no_dict(self):
        paths = ["path1", "path2"]

        app = "nodict"
        doc = {"name": "test", "app": app}

        project = module.Project(doc)
        with self.assertRaises(ValueError):
            project.resolve_and_merge_references(paths)

    def test_folder_no_path(self):
        project = module.Project.from_dict({})
        self.assertIsNone(project.folder())

    @mock.patch("os.path.dirname", return_value="$%%DIRNAME%%$")
    def test_folder(self, dirname_mock: Mock):
        project = module.Project.from_dict({"$path": "$%%PATH%%$"})
        self.assertEqual("$%%DIRNAME%%$", project.folder())
        dirname_mock.assert_called_once_with("$%%PATH%%$")

    def test_src_folder_no_path(self):
        project = module.Project.from_dict({})
        self.assertIsNone(project.src_folder())

    @mock.patch("os.path.dirname", return_value="$DIRNAME")
    def test_src_folder(self, dirname_mock: Mock):
        project = module.Project.from_dict({"$path": "$PATH", "src": "$SRC"})
        self.assertEqual(os.path.join("$DIRNAME", "$SRC"), project.src_folder())
        dirname_mock.assert_called_once_with("$PATH")
