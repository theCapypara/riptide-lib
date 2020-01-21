import os
from pathlib import PurePosixPath

from riptide.lib.cross_platform import cpuser
from riptide.tests.integration.project_loader import load
from riptide.tests.integration.testcase_engine import EngineTest


class PerfDontSyncNamedVolumesWithHostTest(EngineTest):

    def test_dont_sync_named_volume(self):
        pass  # XXX: PyCharm has a problem with docstrings in tests with subtests
        """
        Tests, that if the performance setting is enabled named volumes are 
        created and host mounts are not created
        """
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.'],
                                'integration_perf_dont_sync_named_volumes_with_host.yml'):
            with project_ctx as loaded:
                project = loaded.config["project"]
                service_name = "additional_volumes"
                service = project["app"]["services"][service_name]

                # host paths
                host_in_volume_path_rw = os.path.join(
                    loaded.temp_dir, '_riptide', 'data', service_name, 'in_volume_path_rw'
                )
                host_in_volume_path_named = os.path.join(
                    loaded.temp_dir, '_riptide', 'data', service_name, 'named'
                )

                # container paths
                cnt_in_volume_path_rw = '/in_volume_path_rw'
                cnt_in_volume_path_named = '/in_volume_path_named'

                # Create host paths. Only the one for rw must be the one actually used, because it doesn't have
                # a name.
                os.makedirs(host_in_volume_path_rw)
                os.makedirs(host_in_volume_path_named)

                # Create some files
                open(os.path.join(host_in_volume_path_rw, 'rw1'), 'a').close()
                # This file must not be visible in container, because a named value is used instead!:
                open(os.path.join(host_in_volume_path_named, 'named'), 'a').close()


                # START
                self.run_start_test(loaded.engine,
                                    project,
                                    [service_name],
                                    loaded.engine_tester)

                # Assert volume mounts in container there
                loaded.engine_tester.assert_file_exists(cnt_in_volume_path_rw, loaded.engine, project, service)
                loaded.engine_tester.assert_file_exists(cnt_in_volume_path_named, loaded.engine, project, service)

                # Assert that only the file from the rw host path is visible, because it doesn't have a name set
                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_in_volume_path_rw).joinpath('rw1'),
                                                        loaded.engine, project, service)
                self.assert_file_not_in_container(cnt_in_volume_path_named, loaded, project, service, 'named')

                # Add files on host
                open(os.path.join(host_in_volume_path_rw, 'rw_added'), 'a').close()
                open(os.path.join(host_in_volume_path_named, 'named_added'), 'a').close()

                # Assert added file there in rw container
                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_in_volume_path_rw).joinpath('rw_added'),
                                                        loaded.engine, project, service)
                # Assert added file NOT there in named container
                self.assert_file_not_in_container(cnt_in_volume_path_named, loaded, project, service, 'named_added')

                # Add files in container
                loaded.engine_tester.create_file(PurePosixPath(cnt_in_volume_path_rw).joinpath('rw_added_in_container'),
                                                 loaded.engine, project, service, as_user=cpuser.getuid())
                loaded.engine_tester.create_file(PurePosixPath(cnt_in_volume_path_named).joinpath('named_added_in_container'),
                                                 loaded.engine, project, service, as_user=cpuser.getuid())

                # Assert added file there on host for rw
                self.assertTrue(os.path.isfile(os.path.join(host_in_volume_path_rw, 'rw_added_in_container')))
                # Assert added file NOT there on host for named
                self.assertFalse(os.path.isfile(os.path.join(host_in_volume_path_named, 'named_added_in_container')))

                # STOP
                self.run_stop_test(loaded.engine,
                                   project,
                                   [service_name],
                                   loaded.engine_tester)

                #######
                # Assert that after restarting the contents of the volume are still there, so it's really
                # using the same volume:

                # START
                self.run_start_test(loaded.engine,
                                    project,
                                    [service_name],
                                    loaded.engine_tester)

                loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_in_volume_path_named).joinpath('named_added_in_container'),
                                                        loaded.engine, project, service)

                # STOP
                self.run_stop_test(loaded.engine,
                                   project,
                                   [service_name],
                                   loaded.engine_tester)

                # Assert that a named volume matching the name specified
                # in the volume config witht the priefx riptide__ exists
                loaded.engine_tester.assert_named_volume(loaded.engine, 'riptide__namedvolume-integrationtest')

    def assert_file_not_in_container(self, cnt_in_volume_path_named, loaded, project, service, path):
        try:
            loaded.engine_tester.assert_file_exists(PurePosixPath(cnt_in_volume_path_named).joinpath(path),
                                                    loaded.engine, project, service)
        except AssertionError:
            # The file must actually NOT exist so this is fine
            pass
        else:
            raise AssertionError(
                "The file from the host path of the named volume must not exist in the container, because "
                "the volume must not be mounted to the host system."
            )
