import asyncio

import unittest
from urllib import request


class EngineTest(unittest.TestCase):
    def run_start_test(self, engine, project, services, engine_tester):
        # Run async test code
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._start_async_test(engine, project, services, engine_tester))

    def run_stop_test(self, engine, project, services, engine_tester):
        # Run async test code
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._stop_async_test(engine, project, services, engine_tester))

    def assert_running(self, engine, project, services, engine_tester):
        for service in services:
            if "port" in service:
                # 2. Check if services with port can be resolved to an ip address
                address = engine.address_for(project, service)
                self.assertIsNotNone(address,
                                     'After starting a service with a port configured, it has to be resolvable.')

                # 3. Check if these services can be reached via HTTP
                http_address = 'http://' + address[0] + ':' + address[1]
                try:
                    request.urlopen(http_address)
                except OSError as err:
                    raise AssertionError("A service must be reachable on it's "
                                         "address after start. Service: %s, address: %s"
                                         % (service['$name'], http_address)) from err

        # 4. Let engine tester check details
        engine_tester.assert_running(project, services)

    def assert_not_running(self, engine, project, services, engine_tester):
        for service in services:
            # 2. Check if all services can no longer be resolved to an ip address
            address = engine.address_for(project, service)
            self.assertIsNone(address,
                              'After stopping a service it must not be resolvable to an ip address + port.')

        # 3. Let engine tester check details
        engine_tester.assert_not_running(project, services)

    async def _start_async_test(self, engine, project, services, engine_tester):
        """Start a project with the given services and run all assertions on it"""
        failures = []
        async for service_name, status, finished in engine.start_project(project, services):
            # We are only interested in failed starts, we collect them and throw them together as errors
            if status and finished:
                failures.append(str(status))

        # 1. No services must fail start
        self.assertListEqual([], failures, 'No service must fail starting')

        self.assert_running(engine, project, services, engine_tester)

    async def _stop_async_test(self, engine, project, services, engine_tester):
        """Stop a project with the given services and run all assertions on it"""
        failures = []
        async for service_name, status, finished in engine.stop_project(project, services):
            # We are only interested in failed starts, we collect them and throw them together as errors
            if status and finished:
                failures.append(str(status))

        # 1. No services must fail start
        self.assertListEqual([], failures, 'No service must fail stoping')

        self.assert_not_running(engine, project, services, engine_tester)
