import os
import unittest

from unittest import mock

from unittest.mock import Mock, MagicMock

from configcrunch.tests.test_utils import YamlConfigDocumentStub
from riptide.config.document.service import FOLDER_FOR_LOGGING, create_logging_path, get_logging_path_for
from riptide.tests.stubs import ProjectStub
from riptide.util import get_riptide_version


class UtilTestCase(unittest.TestCase):

    def test_get_riptide_version(self):
        versions = [
            ('0',                (0, None, None)),
            ('dev',              ('dev', None, None)),
            ('0.0',              (0, 0, None)),
            ('1.0',              (1, 0, None)),
            ('1.1',              (1, 1, None)),
            ('1.dev',            (1, 'dev', None)),
            ('dev.dev',          ('dev', 'dev', None)),
            ('1.2.3',            (1, 2, 3)),
            ('1.2.3.4',          (1, 2, 3)),
            ('1.2.3-3',          (1, 2, '3-3')),
            ('dev.dev.dev',      ('dev', 'dev', 'dev')),
        ]
        i = 0
        for version, expected in versions:
            with mock.patch('pkg_resources.get_distribution') as gd_mock:
                version_mock = Mock()
                version_mock.version = version
                gd_mock.return_value = version_mock

                self.assertEqual(expected, get_riptide_version(), 'for entry %i' % i)

                gd_mock.assert_called_with('riptide_lib')
            i += 1
