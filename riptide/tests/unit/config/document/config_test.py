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

    def test_validate_valids(self):
        valid_names = [
            'valid.yml', 'valid_auto_perf.yml', 'integration_perf_dont_sync_unimportant_src.yml',
            'integration_perf_dont_sync_named_volumes_with_host.yml'
        ]
        for name in valid_names:
            with self.subTest(name=name):
                config = module.Config.from_yaml(get_fixture_path(
                    FIXTURE_BASE_PATH + name
                ))
                self.assertTrue(config.validate())

    def test_validate_invalid_missing_engine(self):
        config = module.Config.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_missing_engine.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing key: 'engine'"):
            config.validate()

    def test_validate_invalid_missing_proxy(self):
        config = module.Config.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_missing_proxy.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing key: 'proxy'"):
            config.validate()

    def test_validate_invalid_missing_repos(self):
        config = module.Config.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_missing_repos.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing key: 'repos'"):
            config.validate()

    def test_validate_invalid_missing_performance(self):
        config = module.Config.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_missing_performance.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing key: 'performance'"):
            config.validate()

    def test_validate_invalid_proxy(self):
        config = module.Config.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_proxy.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "should be instance of 'dict'"):
            config.validate()

