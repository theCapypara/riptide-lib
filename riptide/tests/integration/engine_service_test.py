import json
import os
import platform
import re
from time import sleep

import requests
import stat
from pathlib import PurePosixPath

import unittest

from riptide.config.files import CONTAINER_SRC_PATH
from riptide.lib.cross_platform import cpuser
from riptide.tests.integration.project_loader import load
from riptide.tests.integration.testcase_engine import EngineTest


class EngineServiceTest(EngineTest):

    # without src is implicitly tested via EngineStartStopTest.test_simple_result
    def test_with_src(self):
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.', 'src']):
            with project_ctx as loaded:
                project = loaded.config["project"]
                service_name = "simple_with_src"

                # Put a index.html file into the root of the project folder and one in the src folder, depending on
                # what src we are testing right now, we will expect a different file to be served.
                index_file_in_dot = b'hello dot\n'
                index_file_in_src = b'hello src\n'

                with open(os.path.join(loaded.temp_dir, 'index.html'), 'wb') as f:
                    f.write(index_file_in_dot)
                os.makedirs(os.path.join(loaded.temp_dir, 'src'))
                with open(os.path.join(loaded.temp_dir, 'src', 'index.html'), 'wb') as f:
                    f.write(index_file_in_src)

                # START
                self.run_start_test(loaded.engine, project, [service_name], loaded.engine_tester)

                # Check response
                if loaded.src == '.':
                    self.assert_response(index_file_in_dot, loaded.engine, project, service_name)
                elif loaded.src == 'src':
                    self.assert_response(index_file_in_src, loaded.engine, project, service_name)
                else:
                    AssertionError('Error in test: Unexpected src')

                # Check permissions
                user, group, mode, write_check = loaded.engine_tester.get_permissions_at('.', loaded.engine, project,
                                                                                         project["app"]["services"][service_name],
                                                                                         as_user=cpuser.getuid())

                # we use the cpuser module so this technically also works on windows because the cpuser module returns 0
                # and Docker mounts for root.
                self.assertEqual(cpuser.getuid(), user, 'The current user needs to own the src volumes')
                self.assertEqual(cpuser.getgid(), group, 'The current group needs to be the group of the src volumes')
                self.assertTrue(bool(mode & stat.S_IRUSR), 'The src volume must be readable by owner')
                self.assertTrue(bool(mode & stat.S_IWUSR), 'The src volume must be writable by owner')
                self.assertTrue(write_check, 'The src volume must be ACTUALLY writable by owner')

                # STOP
                self.run_stop_test(loaded.engine, project, [service_name], loaded.engine_tester)

    def test_custom_command(self):
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.']):
            with project_ctx as loaded:
                project = loaded.config["project"]
                service_name = "custom_command"

                # START
                self.run_start_test(loaded.engine, project, [service_name], loaded.engine_tester)

                # Check response
                # The custom command disables auto-index of http-server so we should get a directory
                # listing instead
                self.assert_response_matches_regex('<title>Index of /</title>', loaded.engine, project, service_name)

                # STOP
                self.run_stop_test(loaded.engine, project, [service_name], loaded.engine_tester)

    def test_environment(self):
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.']):
            with project_ctx as loaded:
                engine = loaded.engine
                project = loaded.config["project"]
                service_name = "env"
                service = loaded.config["project"]["app"]["services"][service_name]

                # START
                self.run_start_test(loaded.engine, project, [service_name], loaded.engine_tester)

                self.assertEqual('TEST_ENV_VALUE', loaded.engine_tester.get_env('TEST_ENV_KEY',
                                                                                engine, project, service))
                self.assertIsNone(loaded.engine_tester.get_env('TEST_ENV_DOES_NOT_EXIST',
                                                               engine, project, service))

                # STOP
                self.run_stop_test(loaded.engine, project, [service_name], loaded.engine_tester)

    def test_configs(self):
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.']):
            with project_ctx as loaded:
                engine = loaded.engine
                project = loaded.config["project"]
                service_name = "configs"
                service = project["app"]["services"][service_name]

                # START
                self.run_start_test(loaded.engine, project, [service_name], loaded.engine_tester)

                # Assert existing and content
                self.assertEqual('no_variable_just_text', loaded.engine_tester.get_file('/config1', loaded.engine,
                                                                                        project, service))

                self.assertEqual(project["app"]["name"],  loaded.engine_tester.get_file('/config2', loaded.engine,
                                                                                        project, service))

                # Assert permissions
                user1, group1, mode1, write_check1 = loaded.engine_tester.get_permissions_at('/config1', loaded.engine,
                                                                                             project, service,
                                                                                             is_directory=False,
                                                                                             as_user=cpuser.getuid())

                self.assertEqual(cpuser.getuid(), user1, 'The current user needs to own the config file')
                self.assertEqual(cpuser.getgid(), group1, 'The current group needs to be the group of the config file')
                self.assertTrue(bool(mode1 & stat.S_IRUSR), 'The config file must be readable by owner')
                self.assertTrue(bool(mode1 & stat.S_IWUSR), 'The config file must be writable by owner')
                self.assertTrue(write_check1, 'The config file must be ACTUALLY writable by owner')

                user2, group2, mode2, write_check2 = loaded.engine_tester.get_permissions_at('/config2', loaded.engine,
                                                                                             project, service,
                                                                                             is_directory=False,
                                                                                             as_user=cpuser.getuid())

                self.assertEqual(cpuser.getuid(), user2, 'The current user needs to own the config file')
                self.assertEqual(cpuser.getgid(), group2, 'The current group needs to be the group of the config file')
                self.assertTrue(bool(mode2 & stat.S_IRUSR), 'The config file must be readable by owner')
                self.assertTrue(bool(mode2 & stat.S_IWUSR), 'The config file must be writable by owner')
                self.assertTrue(write_check2, 'The config file must be ACTUALLY writable by owner')

                # Assert that files _riptide/config/NAME_WITH_DASHES have been created
                self.assertTrue(os.path.isfile(os.path.join(loaded.temp_dir, '_riptide', 'processed_config',
                                                            service_name, 'one')))
                self.assertTrue(os.path.isfile(os.path.join(loaded.temp_dir, '_riptide', 'processed_config',
                                                            service_name, 'two')))

                # STOP
                self.run_stop_test(loaded.engine, project, [service_name], loaded.engine_tester)

    def test_with_working_directory(self):
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.', 'src']):
            with project_ctx as loaded:
                project = loaded.config["project"]
                services = ["src_working_directory", "working_directory_absolute"]

                # Put index.html into following folder:
                # - <project>/workdir
                # - <project>/src/workdir
                index_file_in_src_workdir = b'hello src_workdir\n'
                index_file_in_workdir = b'hello workdir\n'

                os.makedirs(os.path.join(loaded.temp_dir, 'workdir'))
                os.makedirs(os.path.join(loaded.temp_dir, 'src', 'workdir'))
                with open(os.path.join(loaded.temp_dir, 'workdir', 'index.html'), 'wb') as f:
                    f.write(index_file_in_workdir)
                with open(os.path.join(loaded.temp_dir, 'src', 'workdir', 'index.html'), 'wb') as f:
                    f.write(index_file_in_src_workdir)

                # START
                self.run_start_test(loaded.engine, project, services, loaded.engine_tester)

                # Check response
                for service_name in services:
                    if service_name == 'src_working_directory':
                        if loaded.src == '.':
                            self.assert_response(index_file_in_workdir, loaded.engine, project, service_name)
                        elif loaded.src == 'src':
                            self.assert_response(index_file_in_src_workdir, loaded.engine, project, service_name)
                        else:
                            AssertionError('Error in test: Unexpected src')
                    elif service_name == 'working_directory_absolute':
                        # We didn't put an index.html at /a_folder, so we expect
                        # a directory listing of the three files we put in the image
                        self.assert_response_matches_regex(re.compile('<title>Index of /</title>.*'
                                                                      '<a href="/file1">file1</a>.*'
                                                                      '<a href="/file2">file2</a>.*'
                                                                      '<a href="/file3">file3</a>'
                                                           , re.MULTILINE | re.DOTALL),
                                                           loaded.engine, project, service_name)
                    else:
                        AssertionError('Error in test: Unexpected service')

                # STOP
                self.run_stop_test(loaded.engine, project, services, loaded.engine_tester)

    def test_additional_volumes(self):
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.', 'src']):
            with project_ctx as loaded:
                project = loaded.config["project"]
                service_name = "additional_volumes"
                service = project["app"]["services"][service_name]

                # host paths
                host_in_volume_path_rw = os.path.join(loaded.temp_dir, '_riptide', 'data', service_name, 'in_volume_path_rw')
                host_in_volume_path_rw_explicit = os.path.join(loaded.temp_dir, '_riptide', 'data', service_name, 'in_volume_path_rw_explicit')
                host_in_volume_path_ro = os.path.join(loaded.temp_dir, '_riptide', 'data', service_name, 'in_volume_path_ro')
                host_relative_to_project = os.path.join(loaded.temp_dir, 'relative_to_project')
                host_test_auto_create = os.path.join(loaded.temp_dir, '_riptide', 'data', service_name, 'test_auto_create')

                # container paths
                cnt_in_volume_path_rw = '/in_volume_path_rw'
                cnt_in_volume_path_rw_explicit = '/in_volume_path_rw_explicit'
                cnt_in_volume_path_ro = '/in_volume_path_ro'
                cnt_relative_to_project = str(PurePosixPath(CONTAINER_SRC_PATH).joinpath('relative_to_src'))
                cnt_test_auto_create = '/test_auto_create'

                # Create most volume mounts
                os.makedirs(host_in_volume_path_rw)
                os.makedirs(host_in_volume_path_rw_explicit)
                os.makedirs(host_in_volume_path_ro)
                os.makedirs(host_relative_to_project)

                # create 'src'
                os.makedirs(os.path.join(loaded.temp_dir, loaded.src), exist_ok=True)

                ###
                # Create some files
                open(os.path.join(host_in_volume_path_rw, 'rw1'), 'a').close()
                open(os.path.join(host_in_volume_path_rw, 'rw2'), 'a').close()

                # (no in rw_explicit)

                open(os.path.join(host_in_volume_path_ro, 'ro1'), 'a').close()

                open(os.path.join(host_relative_to_project, 'rtp1'), 'a').close()
                open(os.path.join(host_relative_to_project, 'rtp2'), 'a').close()
                open(os.path.join(host_relative_to_project, 'rtp3'), 'a').close()

                ###

                # START
                self.run_start_test(loaded.engine, project, [service_name], loaded.engine_tester)

                # Assert volume mounts on host there
                self.assertTrue(os.path.isdir(host_in_volume_path_rw))
                self.assertTrue(os.path.isdir(host_in_volume_path_rw_explicit))
                self.assertTrue(os.path.isdir(host_in_volume_path_ro))
                self.assertTrue(os.path.isdir(host_relative_to_project))
                self.assertTrue(os.path.isdir(host_test_auto_create))

                # Assert volume mounts in container there
                loaded.engine_tester.assert_file_exists(cnt_in_volume_path_rw, loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(cnt_in_volume_path_rw_explicit, loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(cnt_in_volume_path_ro, loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(cnt_relative_to_project, loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(cnt_test_auto_create, loaded.engine, project, service)

                # Assert files there in container
                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_in_volume_path_rw).joinpath('rw1'),
                                                        loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_in_volume_path_rw).joinpath('rw2'),
                                                        loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_in_volume_path_ro).joinpath('ro1'),
                                                        loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_relative_to_project).joinpath('rtp1'),
                                                        loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_relative_to_project).joinpath('rtp2'),
                                                        loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_relative_to_project).joinpath('rtp3'),
                                                        loaded.engine, project, service)

                # Assert relative_to_src diectory there on host
                # (from mounting relative_to_project it inside /src on container )
                host_relative_to_src = os.path.join(loaded.temp_dir, loaded.src, 'relative_to_src')
                self.assertTrue(os.path.isdir(host_relative_to_src))
                # Even though the directory must exist, the files must NOT due to the way mounting works on linux.
                self.assertFalse(os.path.isfile(os.path.join(host_relative_to_src, 'rtp1')))
                self.assertFalse(os.path.isfile(os.path.join(host_relative_to_src, 'rtp2')))
                self.assertFalse(os.path.isfile(os.path.join(host_relative_to_src, 'rtp3')))

                # Add files on host
                open(os.path.join(host_in_volume_path_rw, 'rw_added'), 'a').close()
                open(os.path.join(host_in_volume_path_rw_explicit, 'rw_explicit_added'), 'a').close()

                # Assert added files there in container
                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_in_volume_path_rw).joinpath('rw_added'),
                                                        loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_in_volume_path_rw_explicit).joinpath('rw_explicit_added'),
                                                        loaded.engine, project, service)

                # Add files in container
                loaded.engine_tester.create_file(PurePosixPath(cnt_in_volume_path_rw).joinpath('rw_added_in_container'),
                                                 loaded.engine, project, service, as_user=cpuser.getuid())

                # Assert added files there on host
                self.assertTrue(os.path.isfile(os.path.join(host_in_volume_path_rw, 'rw_added_in_container')))

                # Assert permissions rw
                user1, group1, mode1, write_check = loaded.engine_tester.get_permissions_at('/in_volume_path_rw',
                                                                                            loaded.engine, project, service,
                                                                                            as_user=cpuser.getuid())

                self.assertEqual(cpuser.getuid(), user1, 'The current user needs to own the volume')
                self.assertEqual(cpuser.getgid(), group1, 'The current group needs to be the group of the volume')
                self.assertTrue(bool(mode1 & stat.S_IRUSR), 'The volume must be readable by user')
                self.assertTrue(bool(mode1 & stat.S_IWUSR), 'The volume must be writable by group')
                self.assertTrue(write_check, 'The volume has to be ACTUALLY writable by user; files must be creatable.')

                # Assert permissions ro
                user, group, mode, write_check = loaded.engine_tester.get_permissions_at('/in_volume_path_ro',
                                                                                         loaded.engine, project, service,
                                                                                         as_user=cpuser.getuid())

                self.assertEqual(cpuser.getuid(), user1, 'The current user needs to own the volume')
                self.assertEqual(cpuser.getgid(), group1, 'The current group needs to be the group of the volume')
                self.assertTrue(bool(mode1 & stat.S_IRUSR), 'The volume must be readable by user')
                self.assertTrue(bool(mode1 & stat.S_IWUSR), 'The volume must be writable by group')
                self.assertFalse(write_check, 'The volume has to be NOT ACTUALLY writable by user; '
                                              'files must NOT be creatable.')

                # STOP
                self.run_stop_test(loaded.engine, project, [service_name], loaded.engine_tester)

    def test_logging(self):
        MAIN_COMMAND_STDOUT = b"1, 2, 3 test\n"
        MAIN_COMMAND_STDERR = b"1, 2, 3 error\n"
        LOGGING_COMMAND_OUTPUT = b"1 2 3 4 this is command logging test\n"

        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.', 'src']):
            with project_ctx as loaded:
                project = loaded.config["project"]
                services = ["logging", "simple"]

                # START
                self.run_start_test(loaded.engine, project, services, loaded.engine_tester)

                # Give the app a few seconds
                sleep(8)

                # Must still be running
                self.assert_running(loaded.engine, project, services, loaded.engine_tester)

                path_to_logging = os.path.join(loaded.temp_dir, '_riptide', 'logs')
                ### Logging service
                # Assert all logging files are there
                self.assertTrue(os.path.exists(os.path.join(path_to_logging, 'logging', 'stdout.log')))
                self.assertTrue(os.path.exists(os.path.join(path_to_logging, 'logging', 'stderr.log')))
                self.assertTrue(os.path.exists(os.path.join(path_to_logging, 'logging', 'one.log')))
                self.assertTrue(os.path.exists(os.path.join(path_to_logging, 'logging', 'two.log')))

                # Assert contents of files
                with open(os.path.join(path_to_logging, 'logging', 'stdout.log'), 'r') as file:
                    # Engines may add custom buffer on service restarts
                    self.assertTrue(MAIN_COMMAND_STDOUT.decode('utf-8') in file.read())

                with open(os.path.join(path_to_logging, 'logging', 'stderr.log'), 'r') as file:
                    # Engines may add custom buffer on service restarts
                    self.assertTrue(MAIN_COMMAND_STDERR.decode('utf-8') in file.read())

                with open(os.path.join(path_to_logging, 'logging', 'one.log'), 'rb') as file:
                    self.assertEqual(MAIN_COMMAND_STDOUT, file.read())

                with open(os.path.join(path_to_logging, 'logging', 'two.log'), 'rb') as file:
                    self.assertEqual(LOGGING_COMMAND_OUTPUT, file.read())

                ### Non logging service
                self.assertFalse(os.path.exists(os.path.join(path_to_logging, 'simple', 'stdout.log')))
                self.assertFalse(os.path.exists(os.path.join(path_to_logging, 'simple', 'stderr.log')))
                self.assertFalse(os.path.exists(os.path.join(path_to_logging, 'simple', 'one.log')))
                self.assertFalse(os.path.exists(os.path.join(path_to_logging, 'simple', 'two.log')))

                # STOP
                self.run_stop_test(loaded.engine, project, services, loaded.engine_tester)

    def test_additional_ports(self):
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.']):
            with project_ctx as loaded:
                project = loaded.config["project"]
                service1 = "additional_ports"
                service2 = "additional_ports_again"

                # Test One: Only one services

                # START
                self.run_start_test(loaded.engine, project, [service1], loaded.engine_tester)

                # Check if localhost:9965 get's us the contents of the service
                response = requests.get('http://127.0.0.1:9965/hostname')
                self.assertEqual(200, response.status_code)
                self.assertEqual(response.content, b'additional_ports\n')

                # STOP
                self.run_stop_test(loaded.engine, project, [service1], loaded.engine_tester)

                # Test Two: Two times same service, second service must have other host port (+1)
                #           We start second service first, to really make sure it doesn't use the first port

                # START
                self.run_start_test(loaded.engine, project, [service2], loaded.engine_tester)
                self.run_start_test(loaded.engine, project, [service1], loaded.engine_tester)

                # Check both services on expected ports
                response = requests.get('http://127.0.0.1:9965/hostname')
                self.assertEqual(200, response.status_code)
                self.assertEqual(response.content, b'additional_ports\n')
                response = requests.get('http://127.0.0.1:9966/hostname')
                self.assertEqual(200, response.status_code)
                self.assertEqual(response.content, b'additional_ports_again\n',
                                 "The second service must register an additional port on host of 9965 + 1")

                # STOP
                self.run_stop_test(loaded.engine, project, [service1, service2], loaded.engine_tester)

                # Test contents of ports.json
                with open(os.path.join(loaded.temp_system_dir, 'ports.json')) as file:
                    json_ports = json.load(file)

                self.assertDictEqual({
                    "ports": {
                        "9965": True,
                        "9966": True
                    },
                    "requests": {
                        project["name"]: {
                            service1: {"9965": 9965},
                            service2: {"9965": 9966}
                        }
                    }
                }, json_ports)

    @unittest.skipIf(platform.system().lower().startswith('win'),
                     "Skipped on Windows. "
                     "This tets does work on Windows, because of cpuser, but since with root and "
                     "without root makes no difference, it's pointless.")
    def test_run_as_current_user_false(self):
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.']):
            with project_ctx as loaded:
                project = loaded.config["project"]
                service_root = "run_as_current_user_false"
                service_no_root = "simple"

                # Test One: Only one services

                # START
                self.run_start_test(loaded.engine, project, [service_root, service_no_root], loaded.engine_tester)

                self.assert_response(b'12345\n',
                                     loaded.engine, project, service_root, "/rootcheck",
                                     "When running with run_as_current_user == false, a service must with "
                                     "user and group of image")

                # TODO: Group is currently not guaranteed to be the same. Change in the future?
                self.assert_response(str.encode('%s\n' % cpuser.getuid()),
                                     loaded.engine, project, service_no_root, "/rootcheck",
                                     "When running without run_as_current_user, a service must "
                                     "with user and group of the user that ran Riptide")

                # STOP
                self.run_stop_test(loaded.engine, project, [service_root, service_no_root], loaded.engine_tester)
