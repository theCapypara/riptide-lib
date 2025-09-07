import os
import unittest
from collections import OrderedDict
from pathlib import PurePosixPath
from tempfile import TemporaryDirectory
from unittest import mock
from unittest.mock import Mock

from riptide.config.files import CONTAINER_SRC_PATH
from riptide.config.service.volumes import process_additional_volumes

# For convenience use in other unit tests
STUB_PAV__KEY = "__process_additional_volumes_called"
STUB_PAV__VAL = "i_was_called!"


class VolumesTestCase(unittest.TestCase):
    def test_process_additional_volumes_simple(self):
        with TemporaryDirectory() as test_dir:
            home_dir = os.path.join(test_dir, "HOME")
            work_dir = os.path.join(test_dir, "WORKDIR")
            existing_absolute_file = os.path.join(test_dir, "absolute_with_ro")

            os.makedirs(home_dir)
            os.makedirs(work_dir)
            open(existing_absolute_file, "a").close()

            with mock.patch("os.path.expanduser", return_value=home_dir):
                input = [
                    {"host": "~/hometest", "container": "/vol1", "mode": "rw"},
                    {"host": "./reltest1", "container": "/vol2", "mode": "rw"},
                    {"host": "reltest2", "container": "/vol3", "mode": "rw"},
                    {"host": "reltestc", "container": "reltest_container", "mode": "rw"},
                    {"host": existing_absolute_file, "container": "/vol4", "mode": "ro"},
                    {"host": os.path.join(test_dir, "absolute_no_mode"), "container": "/vol5"},
                ]
                expected = OrderedDict(
                    {
                        os.path.join(home_dir, "hometest"): {"bind": "/vol1", "mode": "rw"},
                        os.path.join(work_dir, "./reltest1"): {"bind": "/vol2", "mode": "rw"},
                        os.path.join(work_dir, "reltest2"): {"bind": "/vol3", "mode": "rw"},
                        os.path.join(work_dir, "reltestc"): {
                            "bind": str(PurePosixPath(CONTAINER_SRC_PATH).joinpath("reltest_container")),
                            "mode": "rw",
                        },
                        existing_absolute_file: {"bind": "/vol4", "mode": "ro"},
                        os.path.join(test_dir, "absolute_no_mode"): {"bind": "/vol5", "mode": "rw"},
                    }
                )

                actual = process_additional_volumes(input, work_dir)
                self.assertEqual(expected, actual)

                self.assertTrue(os.path.isdir(os.path.join(home_dir, "hometest")))
                self.assertTrue(os.path.isdir(os.path.join(work_dir, "reltest1")))
                self.assertTrue(os.path.isdir(os.path.join(work_dir, "reltest2")))
                self.assertTrue(os.path.isdir(os.path.join(work_dir, "reltestc")))
                self.assertTrue(os.path.isfile(existing_absolute_file))
                self.assertTrue(os.path.isdir(os.path.join(test_dir, "absolute_no_mode")))

    def test_process_additional_volumes_with_type(self):
        with TemporaryDirectory() as test_dir:
            input = [
                {"host": "file", "container": "/vol1", "type": "file"},
                {"host": "dir", "container": "/vol2", "type": "directory"},
                {"host": "also_dir", "container": "/vol3", "type": "invalid"},
            ]
            expected = OrderedDict(
                {
                    os.path.join(test_dir, "file"): {"bind": "/vol1", "mode": "rw"},
                    os.path.join(test_dir, "dir"): {"bind": "/vol2", "mode": "rw"},
                    os.path.join(test_dir, "also_dir"): {"bind": "/vol3", "mode": "rw"},
                }
            )

            actual = process_additional_volumes(input, test_dir)
            self.assertEqual(expected, actual)

            self.assertTrue(os.path.isfile(os.path.join(test_dir, "file")))
            self.assertTrue(os.path.isdir(os.path.join(test_dir, "dir")))
            self.assertTrue(os.path.isdir(os.path.join(test_dir, "also_dir")))

    def test_process_additional_volumes_with_type_mismatch_should_dir_is_file(self):
        with TemporaryDirectory() as test_dir:
            test_file = os.path.join(test_dir, "test_file")
            open(test_file, "a").close()

            input = [
                {"host": test_file, "container": "/vol1", "type": "directory"},
            ]

            with self.assertRaises(NotADirectoryError):
                process_additional_volumes(input, test_dir)

    def test_process_additional_volumes_with_no_type_exists_and_is_not_directory(self):
        with TemporaryDirectory() as test_dir:
            test_file = os.path.join(test_dir, "test_file")
            open(test_file, "a").close()

            input = [
                {"host": test_file, "container": "/vol1"},
            ]

            process_additional_volumes(input, test_dir)

    def test_process_additional_volumes_with_type_mismatch_should_file_is_dir(self):
        with TemporaryDirectory() as test_dir:
            test_inner_dir = os.path.join(test_dir, "test_inner_dir")
            os.makedirs(test_inner_dir)

            input = [
                {"host": test_inner_dir, "container": "/vol1", "type": "file"},
            ]

            with self.assertRaises(IsADirectoryError):
                process_additional_volumes(input, test_dir)

    @mock.patch("platform.system", return_value="Darwin")
    def test_process_additional_volumes_host_system(self, system_mock: Mock):
        with TemporaryDirectory() as test_dir:
            input = [
                {"host": "source1", "container": "/vol1", "mode": "rw", "host_system": "Darwin"},
                {"host": "source2", "container": "/vol2", "mode": "rw", "host_system": "Linux"},
                {"host": "source3", "container": "/vol3", "mode": "rw"},
            ]
            expected = OrderedDict(
                {
                    os.path.join(test_dir, "source1"): {"bind": "/vol1", "mode": "rw"},
                    os.path.join(test_dir, "source3"): {"bind": "/vol3", "mode": "rw"},
                }
            )

            actual = process_additional_volumes(input, test_dir)
            self.assertEqual(expected, actual)
            self.assertIsInstance(actual, OrderedDict)

            self.assertTrue(os.path.isdir(os.path.join(test_dir, "source1")))
            self.assertFalse(os.path.exists(os.path.join(test_dir, "source2")))
            self.assertTrue(os.path.isdir(os.path.join(test_dir, "source3")))

            system_mock.assert_called()

    def test_process_additional_volumes_volume_name_with_type_directory(self):
        with TemporaryDirectory() as test_dir:
            exists_path = os.path.join(test_dir, "no3")
            os.makedirs(exists_path)

            input = [
                {"host": "no1", "container": "/vol1", "volume_name": "vol1", "type": "directory"},
                {"host": "no2", "container": "/vol2", "volume_name": "volTwo"},
                {"host": exists_path, "container": "/vol3", "volume_name": "volThree"},
            ]
            expected = OrderedDict(
                {
                    os.path.join(test_dir, "no1"): {"bind": "/vol1", "mode": "rw", "name": "vol1"},
                    os.path.join(test_dir, "no2"): {"bind": "/vol2", "mode": "rw", "name": "volTwo"},
                    exists_path: {"bind": "/vol3", "mode": "rw", "name": "volThree"},
                }
            )

            actual = process_additional_volumes(input, test_dir)
            self.assertEqual(expected, actual)

            self.assertTrue(os.path.isdir(os.path.join(test_dir, "no1")))
            self.assertTrue(os.path.isdir(os.path.join(test_dir, "no2")))
            self.assertTrue(os.path.isdir(os.path.join(test_dir, "no3")))

    def test_process_additional_volumes_volume_name_with_type_file_defined(self):
        with TemporaryDirectory() as test_dir:
            input = [
                {"host": "no1", "container": "/vol1", "volume_name": "vol1", "type": "file"},
            ]

            with self.assertRaises(NotADirectoryError):
                process_additional_volumes(input, test_dir)

    def test_process_additional_volumes_volume_name_with_type_file_detected(self):
        with TemporaryDirectory() as test_dir:
            open(os.path.join(test_dir, "no1"), "a").close()
            input = [
                {"host": "no1", "container": "/vol1", "volume_name": "vol1"},
            ]

            with self.assertRaises(NotADirectoryError):
                process_additional_volumes(input, test_dir)
