import os
import unittest
from unittest import mock
from unittest.mock import MagicMock, Mock

from riptide.config.document.service import create_logging_path, get_logging_path_for
from riptide.config.service.logging import FOLDER_FOR_LOGGING
from riptide.tests.configcrunch_test_utils import YamlConfigDocumentStub
from riptide.tests.stubs import ProjectStub


class ConfigFilesTestCase(unittest.TestCase):
    @mock.patch("os.makedirs")
    @mock.patch("riptide.config.service.logging.get_project_meta_folder", return_value="/META")
    def test_create_logging_path(self, get_project_meta_folder_mock: Mock, makedirs_mock: Mock):
        service_name = "__unit_test"

        service = YamlConfigDocumentStub({"$name": service_name})
        service.get_project = MagicMock(return_value=ProjectStub({}))  # type: ignore

        service.freeze()
        create_logging_path(service)  # type: ignore

        makedirs_mock.assert_called_once_with(
            "/META" + os.sep + FOLDER_FOR_LOGGING + os.sep + service_name, exist_ok=True
        )

        get_project_meta_folder_mock.assert_called_once_with(ProjectStub.FOLDER)

    @mock.patch("riptide.config.service.logging.remove_all_special_chars", return_value="SPECIAL_CHARS_REMOVED")
    @mock.patch("riptide.config.service.logging.get_project_meta_folder", return_value="/META")
    @mock.patch("os.chmod")
    @mock.patch("builtins.open")
    def test_get_logging_path_for(
        self, open_mock: Mock, chmod_mock: Mock, get_project_meta_folder_mock: Mock, rasc_mock: Mock
    ):
        service_name = "__unit_test"
        log_name = "xyzxyzxyz"

        service = YamlConfigDocumentStub({"$name": service_name})
        service.get_project = MagicMock(return_value=ProjectStub({}))  # type: ignore

        expected = "/META" + os.sep + FOLDER_FOR_LOGGING + os.sep + service_name + os.sep + "SPECIAL_CHARS_REMOVED.log"

        service.freeze()
        self.assertEqual(expected, get_logging_path_for(service, log_name))  # type: ignore

        get_project_meta_folder_mock.assert_called_once_with(ProjectStub.FOLDER)
        rasc_mock.assert_called_once_with(log_name)

        open_mock.assert_called_once_with(expected, "a")
        chmod_mock.assert_called_once_with(expected, 0o666)
