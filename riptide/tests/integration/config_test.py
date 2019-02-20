import os
import unittest

from riptide.config.document.service import Service
from riptide.tests.helpers import get_fixture_path
from riptide.tests.integration.project_loader import load


class ConfigTest(unittest.TestCase):

    def test_load(self):
        """
        Tests that the loading process finishes
        without an error and fields are as expected
        """
        for project_ctx in load(self,
                                ['integration_all.yml', 'integration_no_command.yml', 'integration_no_service.yml'],
                                ['.', 'src']):
            with project_ctx as loaded:
                self.assertEqual(loaded.src, loaded.config["project"]["src"],
                                 'The loaded project must have the src correctly set')
                self.assertEqual(loaded.engine_name, loaded.config["engine"],
                                 'The loaded system config must have the engine correctly set')

    def test_service_initialize_data_correct_config_file_exists_in_both(self):
        """Tests that Services load the correct config file for a document based on merging hierarchy"""
        base_path = get_fixture_path(os.path.join('service', 'test_config_paths'))
        doc = Service({
            '$ref': 'one/config'
        })
        doc.resolve_and_merge_references([base_path])

        self.assertEqual({
            "test": {
                "from": "config.txt",
                "to": "doesnotmatter",
                "$source": os.path.join(base_path, 'one', 'config.txt')
            }
        }, doc['config'])

    def test_service_initialize_data_correct_config_file_exists_in_referenced_only(self):
        """Tests that Services load the correct config file for a document based on merging hierarchy"""
        base_path = get_fixture_path(os.path.join('service', 'test_config_paths'))
        doc = Service({
            '$ref': 'not_exist_one/config'
        })
        doc.resolve_and_merge_references([base_path])

        self.assertEqual(os.path.realpath(os.path.join(base_path, 'two', 'config.txt')),
                         os.path.realpath(doc['config']["test"]["$source"]))
