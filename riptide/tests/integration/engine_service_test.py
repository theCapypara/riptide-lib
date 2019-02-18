import os
import re
import requests
import stat

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
                user, group, mode = loaded.engine_tester.get_permissions_at('.', loaded.engine, project,
                                                                            project["app"]["services"][service_name])

                # we use the cpuser module so this technically also works on windows because the cpuser module returns 0
                # and Docker mounts for root.
                self.assertEqual(cpuser.getuid(), user, 'The current user needs to own the src volumes')
                self.assertEqual(cpuser.getgid(), group, 'The current group needs to be the group of the src volumes')
                self.assertTrue(bool(mode & stat.S_IRUSR), 'The src volume must be readable by owner')
                self.assertTrue(bool(mode & stat.S_IWUSR), 'The src volume must be writable by owner')

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
                user1, group1, mode1 = loaded.engine_tester.get_permissions_at('/config1', loaded.engine,
                                                                               project, service)

                self.assertEqual(cpuser.getuid(), user1, 'The current user needs to own the config file')
                self.assertEqual(cpuser.getgid(), group1, 'The current group needs to be the group of the config file')
                self.assertTrue(bool(mode1 & stat.S_IRUSR), 'The config file must be readable by owner')
                self.assertTrue(bool(mode1 & stat.S_IWUSR), 'The config file must be writable by owner')

                user2, group2, mode2 = loaded.engine_tester.get_permissions_at('/config2', loaded.engine,
                                                                               project, service)

                self.assertEqual(cpuser.getuid(), user2, 'The current user needs to own the config file')
                self.assertEqual(cpuser.getgid(), group2, 'The current group needs to be the group of the config file')
                self.assertTrue(bool(mode2 & stat.S_IRUSR), 'The config file must be readable by owner')
                self.assertTrue(bool(mode2 & stat.S_IWUSR), 'The config file must be writable by owner')

                # Assert that files _riptide/config/NAME_WITH_DASHES have been created
                self.assertTrue(os.path.isfile(os.path.join(loaded.temp_dir, '_riptide', 'processed_config',
                                                            service_name,'configs-config1-txt')))
                self.assertTrue(os.path.isfile(os.path.join(loaded.temp_dir, '_riptide', 'processed_config',
                                                            service_name,'configs-config2-txt')))

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
