import os

import unittest
from schema import SchemaError

import riptide.config.document.config as module
from riptide.tests.helpers import get_fixture_path

FIXTURE_BASE_PATH = 'config' + os.sep

class ConfigTestCase(unittest.TestCase):

    def test_header(self):
        config = module.Config({})
        self.assertEqual(module.HEADER, config.header())

    def test_validate_valid(self):
        config = module.Config.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'valid.yml'
        ))
        self.assertTrue(config.validate())

    def test_validate_invalid_missing_engine(self):
        config = module.Config.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_missing_engine.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing keys: 'engine'"):
            config.validate()

    def test_validate_invalid_missing_proxy(self):
        config = module.Config.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_missing_proxy.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing keys: 'proxy'"):
            config.validate()

    def test_validate_invalid_missing_repos(self):
        config = module.Config.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_missing_repos.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing keys: 'repos'"):
            config.validate()

    def test_validate_invalid_proxy(self):
        config = module.Config.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_proxy.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "should be instance of 'dict'"):
            config.validate()

