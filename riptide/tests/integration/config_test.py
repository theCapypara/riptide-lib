import unittest

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
