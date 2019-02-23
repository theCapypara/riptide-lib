import os

import requests
import unittest

from riptide.engine import loader as riptide_engine_loader
from riptide.tests.integration.project_loader import load
from riptide.tests.integration.testcase_engine import EngineTest


class EngineStartStopTest(EngineTest):

    def test_engine_loading(self):
        for project_ctx in load(self,
                                ['integration_all.yml', 'integration_some.yml',
                                 'integration_no_command.yml', 'integration_no_service.yml'],
                                ['.']):
            with project_ctx as loaded:
                loaded_engine = riptide_engine_loader.load_engine(loaded.engine_name)
                self.assertIsInstance(loaded_engine, loaded.engine.__class__,
                                      'The engine loader has to return the correct AbstractEngine instance of the engine')

    def test_start_stop(self):
        pass  # XXX: PyCharm has a problem with docstrings in tests with subtests
        """Full start/stop check for all different scenarios"""
        for project_ctx in load(self,
                                ['integration_all.yml', 'integration_no_command.yml', 'integration_no_service.yml'],
                                ['.', 'src']):
            with project_ctx as loaded:
                project = loaded.config["project"]
                services = project["app"]["services"].keys() if "services" in project["app"] else []

                # Create src folder
                os.makedirs(os.path.join(loaded.temp_dir, loaded.src), exist_ok=True)

                # START
                self.run_start_test(loaded.engine, project, services, loaded.engine_tester)

                # STOP
                self.run_stop_test(loaded.engine, project, services, loaded.engine_tester)

    def test_start_stop_subset(self):
        pass  # XXX: PyCharm has a problem with docstrings in tests with subtests
        """Start some services, stop some again, assert that the rest is still running and then stop the rest."""
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.']):
            with project_ctx as loaded:
                project = loaded.config["project"]
                services_to_start_first = ["simple", "simple_with_src", "custom_command", "configs"]
                services_to_stop_first = ["custom_command", "simple_with_src"]
                still_running_after_first = ["configs", "simple"]
                services_to_start_end = project["app"]["services"].keys() if "services" in project["app"] else []

                # Create src folder
                os.makedirs(os.path.join(loaded.temp_dir, loaded.src), exist_ok=True)

                # START first
                self.run_start_test(loaded.engine, project, services_to_start_first, loaded.engine_tester)

                # STOP first
                self.run_stop_test(loaded.engine, project, services_to_stop_first, loaded.engine_tester)

                # Assert the rest is still running
                self.assert_running(loaded.engine, project, still_running_after_first, loaded.engine_tester)

                # START end
                self.run_start_test(loaded.engine, project, services_to_start_end, loaded.engine_tester)

                # STOP end
                self.run_stop_test(loaded.engine, project, services_to_start_end, loaded.engine_tester)

    def test_simple_result(self):
        pass  # XXX: PyCharm has a problem with docstrings in tests with subtests
        """Starts only the simple test service and checks it's http response"""
        for project_ctx in load(self,
                                ['integration_all.yml'],
                                ['.']):
            with project_ctx as loaded:
                project = loaded.config["project"]
                services = ["simple"]

                # START
                self.run_start_test(loaded.engine, project, services, loaded.engine_tester)

                # Check response
                self.assert_response(b'hello riptide\n', loaded.engine, project, "simple")

                # STOP
                self.run_stop_test(loaded.engine, project, services, loaded.engine_tester)
