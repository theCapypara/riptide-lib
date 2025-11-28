import unittest

from riptide.hook.event import HookEvent


class HookEventTestCase(unittest.TestCase):
    def test_try_from_key(self):
        self.assertEqual(HookEvent.GitPostMerge, HookEvent.try_from_key("git-post-merge"))
        self.assertEqual(None, HookEvent.try_from_key("custom-cst"))
        self.assertEqual(None, HookEvent.try_from_key("foo"))

    def test_try_any_from_key(self):
        self.assertEqual(HookEvent.GitPreCommit, HookEvent.try_any_from_key("git-pre-commit"))
        self.assertEqual("custom-bazbaz", HookEvent.try_any_from_key("custom-bazbaz"))
        self.assertEqual(None, HookEvent.try_any_from_key("foo"))

    def test_validate(self):
        self.assertEqual(HookEvent.PreStop, HookEvent.validate(HookEvent.PreStop))
        self.assertEqual("custom-bazbaz", HookEvent.validate("custom-bazbaz"))
        self.assertEqual(None, HookEvent.validate("foo"))
        self.assertEqual(HookEvent.PreStop, HookEvent.validate("pre-stop"))

    def test_is_custom(self):
        self.assertFalse(HookEvent.is_custom(HookEvent.PreStop))
        self.assertTrue(HookEvent.is_custom("custom-bazbaz"))

    def test_key_for(self):
        self.assertEqual("pre-start", HookEvent.key_for(HookEvent.PreStart))
        self.assertEqual("custom-foo", HookEvent.key_for("custom-foo"))
