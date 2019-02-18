import requests
import unittest

from riptide.engine import loader as riptide_engine_loader
from riptide.tests.integration.project_loader import load
from riptide.tests.integration.testcase_engine import EngineTest


class EngineStartStopTest(EngineTest):

    def test_engine_loading(self):
        for project_ctx in load(self,
                                ['integration_all.yml', 'integration_no_command.yml', 'integration_no_service.yml'],
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

                # START
                self.run_start_test(loaded.engine, project, services, loaded.engine_tester)

                # STOP
                self.run_stop_test(loaded.engine, project, services, loaded.engine_tester)

    @unittest.skip('to do not done')
    def test_start_stop_subset(self):
        """TODO"""

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
                (ip, port) = loaded.engine.address_for(project, "simple")
                response = requests.get('http://' + ip + ':' + port)

                self.assertEqual(200, response.status_code)
                self.assertEqual(b'hello riptide\n', response.content)

                # STOP
                self.run_stop_test(loaded.engine, project, services, loaded.engine_tester)