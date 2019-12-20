from collections import OrderedDict

import os
import unittest

from unittest import mock

from pathlib import PurePosixPath
from unittest.mock import Mock, call

from riptide.config.files import CONTAINER_SRC_PATH
from riptide.config.service.volumes import process_additional_volumes
from riptide.tests.stubs import ProjectStub

# For convenience use in other unit tests
STUB_PAV__KEY = '__process_additional_volumes_called'
STUB_PAV__VAL = 'i_was_called!'


class VolumesTestCase(unittest.TestCase):

    @mock.patch("os.path.expanduser", return_value=os.sep + 'HOME')
    @mock.patch("os.makedirs")
    def test_process_additional_volumes(self, makedirs_mock: Mock, expanduser_mock: Mock):
        input = [{
                "host": "~/hometest",
                "container": "/vol1",
                "mode": "rw"
            }, {
                 "host": "./reltest1",
                 "container": "/vol2",
                 "mode": "rw"
             }, {
                "host": "reltest2",
                "container": "/vol3",
                "mode": "rw"
            }, {
                "host": "reltestc",
                "container": "reltest_container",
                "mode": "rw"
            }, {
                "host": "/absolute_with_ro",
                "container": "/vol4",
                "mode": "ro"
            }, {
                "host": "/absolute_no_mode",
                "container": "/vol5"
            }, {
                "host": "/absolute_named",
                "container": "/vol6",
                "volume_name": "I have a name"
            }
        ]
        expected = OrderedDict({
            os.path.join(os.sep + 'HOME', 'hometest'):      {'bind': '/vol1', 'mode': 'rw'},
            os.path.join(ProjectStub.FOLDER, './reltest1'): {'bind': '/vol2', 'mode': 'rw'},
            os.path.join(ProjectStub.FOLDER, 'reltest2'):   {'bind': '/vol3', 'mode': 'rw'},
            os.path.join(ProjectStub.FOLDER, 'reltestc'):
                {'bind': str(PurePosixPath(CONTAINER_SRC_PATH).joinpath('reltest_container')), 'mode': 'rw'},
            '/absolute_with_ro':                            { 'bind': '/vol4', 'mode': 'ro'},
            '/absolute_no_mode':                            {'bind': '/vol5', 'mode': 'rw'},
            '/absolute_named':                              {'bind': '/vol6', 'mode': 'rw', 'name': 'I have a name'}
        })

        actual = process_additional_volumes(input, ProjectStub.FOLDER)
        self.assertEqual(expected, actual)
        self.assertIsInstance(actual, OrderedDict)

        makedirs_mock.assert_has_calls([
            # ADDITIONAL VOLUMES
            call(os.path.join(os.sep + 'HOME', 'hometest'), exist_ok=True),
            call(os.path.join(ProjectStub.FOLDER, './reltest1'), exist_ok=True),
            call(os.path.join(ProjectStub.FOLDER, 'reltest2'), exist_ok=True),
            call(os.path.join(ProjectStub.FOLDER, 'reltestc'), exist_ok=True),
            call(os.path.join('/absolute_with_ro'), exist_ok=True),
            call(os.path.join('/absolute_no_mode'), exist_ok=True),
            call(os.path.join('/absolute_named'), exist_ok=True),
        ], any_order=True)

        # First volume had ~ in it:
        expanduser_mock.assert_called_once_with('~')
