import os
import unittest
from unittest import mock

from unittest.mock import call, Mock

import riptide.config.document.project as module
from configcrunch import ConfigcrunchError
from configcrunch.test_utils import YamlConfigDocumentStub
from riptide.tests.helpers import side_effect_for_load_subdocument


class ProjectTestCase(unittest.TestCase):

    def test_header(self):
        cmd = module.Project({})
        self.assertEqual(module.HEADER, cmd.header())

    @unittest.skip("not done yet")
    def test_validate(self):
        """TODO"""

    @mock.patch("riptide.config.document.project.YamlConfigDocument.resolve_and_merge_references")
    def test_resolve_and_merge_references_no_subdocs(self, super_mock):
        doc = {
            'name': 'test'
        }
        project = module.Project(doc)
        project.resolve_and_merge_references(['./path1', './path2'])
        super_mock.assert_called_once_with(['./path1', './path2'])

    @mock.patch('riptide.config.document.project.YamlConfigDocument.resolve_and_merge_references')
    def test_resolve_and_merge_references_with_app(self, super_mock):
        paths = ['path1', 'path2']

        app = {'key1': 'value1'}
        doc = {
            'name': 'test',
            'app': app
        }

        with mock.patch(
                "riptide.config.document.project.load_subdocument",
                side_effect=side_effect_for_load_subdocument()
        ) as load_subdoc_mock:
            project = module.Project(doc)
            project.resolve_and_merge_references(paths)

            self.assertIsInstance(project['app'], YamlConfigDocumentStub)
            self.assertEqual(app, project['app'].doc)

            super_mock.assert_called_once_with(paths)
            load_subdoc_mock.assert_has_calls([
                call(app, project, module.App, paths),
            ], any_order=True)

    def test_resolve_and_merge_references_with_app_no_dict(self):
        paths = ['path1', 'path2']

        app = 'nodict'
        doc = {
            'name': 'test',
            'app': app
        }

        with mock.patch(
                "riptide.config.document.project.load_subdocument",
                side_effect=side_effect_for_load_subdocument()
        ):
            project = module.Project(doc)
            with self.assertRaises(ConfigcrunchError):
                project.resolve_and_merge_references(paths)

    def test_folder_no_path(self):
        project = module.Project({})
        self.assertIsNone(project.folder())

    @mock.patch('os.path.dirname', return_value='$%%DIRNAME%%$')
    def test_folder(self, dirname_mock: Mock):
        project = module.Project({'$path': '$%%PATH%%$'})
        self.assertEqual('$%%DIRNAME%%$', project.folder())
        dirname_mock.assert_called_once_with('$%%PATH%%$')

    def test_src_folder_no_path(self):
        project = module.Project({})
        self.assertIsNone(project.src_folder())

    @mock.patch('os.path.dirname', return_value='$DIRNAME')
    def test_src_folder(self, dirname_mock: Mock):
        project = module.Project({'$path': '$PATH', 'src': '$SRC'})
        self.assertEqual(os.path.join('$DIRNAME', '$SRC'), project.src_folder())
        dirname_mock.assert_called_once_with('$PATH')
