import unittest

import riptide.config.document.config as module


class ConfigTestCase(unittest.TestCase):

    def test_header(self):
        cmd = module.Config({})
        self.assertEqual(module.HEADER, cmd.header())

    @unittest.skip("not done yet")
    def test_validate(self):
        """TODO"""
