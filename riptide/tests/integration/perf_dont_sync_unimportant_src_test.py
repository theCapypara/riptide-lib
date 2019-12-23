import os
from pathlib import PurePosixPath

from riptide.lib.cross_platform import cpuser
from riptide.tests.integration.project_loader import load, ProjectLoadResult
from riptide.tests.integration.testcase_engine import EngineTest


class PerfDontSyncUnimportantSrcTest(EngineTest):

    def test_dont_sync_unimportant_src(self):
        pass  # XXX: PyCharm has a problem with docstrings in tests with subtests
        """
        Tests, that changes made in the container to paths marked as unimportant are not visible on the host
        system, but all other are, if the performance option for that is set.
        """
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.', 'src'],
                                'integration_perf_dont_sync_unimportant_src.yml'):
            with project_ctx as loaded:
                self._common(loaded, False)

    def test_dont_sync_unimportant_src_feature_disabled(self):
        pass  # XXX: PyCharm has a problem with docstrings in tests with subtests
        """
        Tests that the unimportant paths are normally visible on the host when the feature is disabled.
        """
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.', 'src']):
            with project_ctx as loaded:
                self._common(loaded, True)

    def _common(self, loaded: ProjectLoadResult, files_are_expected_on_host: bool):
        # Directory name, relative to service working dir, that is ignored.
        dir_name = 'unimportant_paths_test'
        # Name of services, mapped to their working directory name as specified in the fixture yaml
        services = {'simple_with_src': '.', 'src_working_directory': 'workdir'}

        project = loaded.config["project"]
        service_objs = project["app"]["services"]

        # host paths
        host_path_synced_simple_with_src = os.path.join(
            loaded.temp_dir, loaded.src, services['simple_with_src'], 'rw'
        )
        host_path_unimportant_simple_with_src = os.path.join(
            loaded.temp_dir, loaded.src, services['simple_with_src'], dir_name
        )
        host_path_synced_src_working_directory = os.path.join(
            loaded.temp_dir, loaded.src, services['src_working_directory'], 'rw'
        )
        host_path_unimportant_src_working_directory = os.path.join(
            loaded.temp_dir, loaded.src, services['src_working_directory'], dir_name
        )

        # container paths
        cnt_path_synced_simple_with_src = '/src/' + services['simple_with_src'] + '/rw'
        cnt_path_unimportant_simple_with_src = '/src/' + services['simple_with_src'] + '/' + dir_name
        cnt_path_synced_src_working_directory = '/src/' + services['src_working_directory'] + '/rw'
        cnt_path_unimportant_src_working_directory = '/src/' + services['src_working_directory'] + '/' + dir_name

        # Create host paths.
        os.makedirs(host_path_synced_simple_with_src)
        os.makedirs(host_path_unimportant_simple_with_src)
        os.makedirs(host_path_synced_src_working_directory)
        os.makedirs(host_path_unimportant_src_working_directory)

        # Create some files
        with open(os.path.join(host_path_synced_simple_with_src, 'rw1'), 'w') as f:
            f.write('rw1host')
        with open(os.path.join(host_path_unimportant_simple_with_src, 'unimportant1'), 'w') as f:
            f.write('unimportant1host')
        with open(os.path.join(host_path_synced_src_working_directory, 'rw2'), 'w') as f:
            f.write('rw2host')
        with open(os.path.join(host_path_unimportant_src_working_directory, 'unimportant2'), 'w') as f:
            f.write('unimportant2host')

        # START
        self.run_start_test(loaded.engine, project, services.keys(), loaded.engine_tester)

        # Assert that all files are visible
        loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_path_synced_simple_with_src).joinpath('rw1'),
                                                loaded.engine, project, service_objs['simple_with_src'])
        loaded.engine_tester.assert_file_exists(
            PurePosixPath(cnt_path_unimportant_simple_with_src).joinpath('unimportant1'),
            loaded.engine, project, service_objs['simple_with_src'])
        loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_path_synced_src_working_directory).joinpath('rw2'),
                                                loaded.engine, project, service_objs['src_working_directory'])
        loaded.engine_tester.assert_file_exists(
            PurePosixPath(cnt_path_unimportant_src_working_directory).joinpath('unimportant2'),
            loaded.engine, project, service_objs['src_working_directory'])

        # Add files in container
        loaded.engine_tester.create_file(
            PurePosixPath(cnt_path_synced_simple_with_src).joinpath('rw1_added_in_container'),
            loaded.engine, project, service_objs['simple_with_src'],
            as_user=cpuser.getuid())
        loaded.engine_tester.create_file(
            PurePosixPath(cnt_path_unimportant_simple_with_src).joinpath('unimportant1_added_in_container'),
            loaded.engine, project, service_objs['simple_with_src'],
            as_user=cpuser.getuid())
        loaded.engine_tester.create_file(
            PurePosixPath(cnt_path_synced_src_working_directory).joinpath('rw2_added_in_container'),
            loaded.engine, project, service_objs['src_working_directory'],
            as_user=cpuser.getuid())
        loaded.engine_tester.create_file(
            PurePosixPath(cnt_path_unimportant_src_working_directory).joinpath('unimportant2_added_in_container'),
            loaded.engine, project, service_objs['src_working_directory'],
            as_user=cpuser.getuid())

        # Assert added file there on host for rws
        self.assertTrue(os.path.isfile(os.path.join(host_path_synced_simple_with_src, 'rw1_added_in_container')))
        self.assertTrue(os.path.isfile(os.path.join(host_path_synced_src_working_directory, 'rw2_added_in_container')))
        # Assert added file NOT there on host for unimportant if option is enabled
        self.assertEqual(
            files_are_expected_on_host,
            os.path.isfile(os.path.join(host_path_unimportant_simple_with_src, 'unimportant1_added_in_container'))
        )
        self.assertEqual(
            files_are_expected_on_host,
            os.path.isfile(os.path.join(host_path_unimportant_src_working_directory, 'unimportant2_added_in_container'))
        )

        # STOP
        self.run_stop_test(loaded.engine, project, services.keys(), loaded.engine_tester)
