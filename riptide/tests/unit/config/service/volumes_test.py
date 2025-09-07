import os
import unittest
from collections import OrderedDict
from pathlib import PurePosixPath
from tempfile import TemporaryDirectory
from unittest import mock
from unittest.mock import Mock, call

from riptide.config.files import CONTAINER_SRC_PATH
from riptide.config.service.volumes import process_additional_volumes
from riptide.tests.stubs import ProjectStub

# For convenience use in other unit tests
STUB_PAV__KEY = "__process_additional_volumes_called"
STUB_PAV__VAL = "i_was_called!"


class VolumesTestCase(unittest.TestCase):
    # TODO: Real fs
    @mock.patch("os.path.expanduser", return_value=os.sep + "HOME")
    @mock.patch("os.makedirs")
    def test_process_additional_volumes_OLD(self, makedirs_mock: Mock, expanduser_mock: Mock):
        input = [
            {"host": "~/hometest", "container": "/vol1", "mode": "rw"},
            {"host": "./reltest1", "container": "/vol2", "mode": "rw"},
            {"host": "reltest2", "container": "/vol3", "mode": "rw"},
            {"host": "reltestc", "container": "reltest_container", "mode": "rw"},
            {"host": "/absolute_with_ro", "container": "/vol4", "mode": "ro"},
            {"host": "/absolute_no_mode", "container": "/vol5"},
            {"host": "/absolute_named", "container": "/vol6", "volume_name": "I have a name"},
        ]
        expected = OrderedDict(
            {
                os.path.join(os.sep + "HOME", "hometest"): {"bind": "/vol1", "mode": "rw"},
                os.path.join(ProjectStub.FOLDER, "./reltest1"): {"bind": "/vol2", "mode": "rw"},
                os.path.join(ProjectStub.FOLDER, "reltest2"): {"bind": "/vol3", "mode": "rw"},
                os.path.join(ProjectStub.FOLDER, "reltestc"): {
                    "bind": str(PurePosixPath(CONTAINER_SRC_PATH).joinpath("reltest_container")),
                    "mode": "rw",
                },
                "/absolute_with_ro": {"bind": "/vol4", "mode": "ro"},
                "/absolute_no_mode": {"bind": "/vol5", "mode": "rw"},
                "/absolute_named": {"bind": "/vol6", "mode": "rw", "name": "I have a name"},
            }
        )

        actual = process_additional_volumes(input, ProjectStub.FOLDER)
        self.assertEqual(expected, actual)
        self.assertIsInstance(actual, OrderedDict)

        makedirs_mock.assert_has_calls(
            [
                # ADDITIONAL VOLUMES
                call(os.path.join(os.sep + "HOME", "hometest"), exist_ok=True),
                call(os.path.join(ProjectStub.FOLDER, "./reltest1"), exist_ok=True),
                call(os.path.join(ProjectStub.FOLDER, "reltest2"), exist_ok=True),
                call(os.path.join(ProjectStub.FOLDER, "reltestc"), exist_ok=True),
                call(os.path.join("/absolute_with_ro"), exist_ok=True),
                call(os.path.join("/absolute_no_mode"), exist_ok=True),
                call(os.path.join("/absolute_named"), exist_ok=True),
            ],
            any_order=True,
        )

        # First volume had ~ in it:
        expanduser_mock.assert_called_once_with("~")

    @mock.patch("platform.system", return_value="Darwin")
    @mock.patch("os.makedirs")
    def test_process_additional_volumes_host_system_OLD(self, makedirs_mock: Mock, system_mock: Mock):
        input = [
            {"host": "/source1", "container": "/vol1", "mode": "rw", "host_system": "Darwin"},
            {"host": "/source2", "container": "/vol2", "mode": "rw", "host_system": "Linux"},
            {"host": "/source3", "container": "/vol3", "mode": "rw"},
        ]
        expected = OrderedDict(
            {
                "/source1": {"bind": "/vol1", "mode": "rw"},
                "/source3": {"bind": "/vol3", "mode": "rw"},
            }
        )

        actual = process_additional_volumes(input, ProjectStub.FOLDER)
        self.assertEqual(expected, actual)
        self.assertIsInstance(actual, OrderedDict)

        makedirs_mock.assert_has_calls(
            [
                # ADDITIONAL VOLUMES
                call("/source1", exist_ok=True),
                call("/source3", exist_ok=True),
            ],
            any_order=True,
        )

        system_mock.assert_called()

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

    @unittest.skip("todo")
    def test_process_additional_volumes_volume_name_with_type_file_defined(self):
        raise NotImplementedError

    @unittest.skip("todo")
    def test_process_additional_volumes_volume_name_with_type_file_detected(self):
        raise NotImplementedError

    @unittest.skip("todo")
    def test_process_additional_volumes_volume_name_with_type_directory_defined(self):
        raise NotImplementedError

    @unittest.skip("todo")
    def test_process_additional_volumes_volume_name_with_type_directory_detected(self):
        raise NotImplementedError
