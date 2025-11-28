import unittest
from unittest import mock

from riptide.config.document import DocumentClass
from riptide.hook.additional_volumes import HookHostPathArgument, apply_hook_mounts
from riptide.hook.manager import HookArgument
from riptide.tests.configcrunch_test_utils import YamlConfigDocumentStub
from riptide.tests.stubs import ProjectStub


class HookAdditionalVolumesTestCase(unittest.TestCase):
    @mock.patch("os.path.abspath", side_effect=lambda path: "//" + path)
    def test_apply_hook_mounts(self, abspath_mock: mock.MagicMock):
        input_config_no_project = YamlConfigDocumentStub.make(DocumentClass.Config, {})
        input_config_with_project = YamlConfigDocumentStub.make(DocumentClass.Config, {})
        input_config_with_project.internal_set("project", ProjectStub.make_project({"src": "SRC"}))
        input_config_no_project.freeze()
        input_config_with_project.freeze()

        input_args_empty: list[HookArgument] = []
        input_args: list[HookArgument] = [
            "arg1",
            HookHostPathArgument("hostpath"),
            HookHostPathArgument("hostpath_ro", read_only=True),
            "arg2",
        ]

        input_additional_host_mounts_empty: dict[str, HookHostPathArgument] = {}
        input_additional_host_mounts = {
            "from_input_rw": HookHostPathArgument("RW"),
            "from_input_ro": HookHostPathArgument("RO", read_only=True),
        }

        self.assertEqual(
            ([], {}), apply_hook_mounts(input_config_no_project, input_args_empty, input_additional_host_mounts_empty)
        )

        self.assertEqual(
            (
                [],
                {ProjectStub.FOLDER: {"bind": "/project", "mode": "rw"}},
            ),
            apply_hook_mounts(input_config_with_project, input_args_empty, input_additional_host_mounts_empty),
        )

        uuid_call_count = 0

        def uuid_side_effect():
            nonlocal uuid_call_count

            uuid_call_count += 1
            return f"UUID-{uuid_call_count}"

        with mock.patch("uuid.uuid4", side_effect=uuid_side_effect):
            self.assertEqual(
                (
                    ["arg1", "/riptide/hook/path/UUID-1", "/riptide/hook/path/UUID-2", "arg2"],
                    {
                        "hostpath": {"bind": "/riptide/hook/path/UUID-1", "mode": "rw"},
                        "hostpath_ro": {"bind": "/riptide/hook/path/UUID-2", "mode": "ro"},
                    },
                ),
                apply_hook_mounts(input_config_no_project, input_args, input_additional_host_mounts_empty),
            )

        self.assertEqual(
            (
                [],
                {
                    "RW": {"bind": "from_input_rw", "mode": "rw"},
                    "RO": {"bind": "from_input_ro", "mode": "ro"},
                },
            ),
            apply_hook_mounts(input_config_no_project, input_args_empty, input_additional_host_mounts),
        )

        with mock.patch("uuid.uuid4", side_effect=uuid_side_effect):
            self.assertEqual(
                (
                    ["arg1", "/riptide/hook/path/UUID-3", "/riptide/hook/path/UUID-4", "arg2"],
                    {
                        ProjectStub.FOLDER: {"bind": "/project", "mode": "rw"},
                        "hostpath": {"bind": "/riptide/hook/path/UUID-3", "mode": "rw"},
                        "hostpath_ro": {"bind": "/riptide/hook/path/UUID-4", "mode": "ro"},
                        "RW": {"bind": "from_input_rw", "mode": "rw"},
                        "RO": {"bind": "from_input_ro", "mode": "ro"},
                    },
                ),
                apply_hook_mounts(input_config_with_project, input_args, input_additional_host_mounts),
            )
