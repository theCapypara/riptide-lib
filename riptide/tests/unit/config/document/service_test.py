import os
import unittest
from collections import OrderedDict
from unittest import mock
from unittest.mock import MagicMock, Mock, call

import riptide.config.document.service as module
from configcrunch import ConfigcrunchError
from riptide.config import loader as LOADER_MODULE
from riptide.config.document import DocumentClass
from riptide.config.files import CONTAINER_HOME_PATH, CONTAINER_SRC_PATH
from riptide.engine.abstract import RIPTIDE_HOST_HOSTNAME
from riptide.tests.configcrunch_test_utils import YamlConfigDocumentStub
from riptide.tests.helpers import get_fixture_path, patch_mock_db_driver
from riptide.tests.stubs import ProjectStub, process_config_stub
from riptide.tests.unit.config.service.volumes_test import STUB_PAV__KEY, STUB_PAV__VAL
from schema import SchemaError

FIXTURE_BASE_PATH = "service" + os.sep


class ServiceTestCase(unittest.TestCase):
    maxDiff = None

    def test_header(self):
        service = module.Service.from_dict({})
        self.assertEqual(module.HEADER, service.header())

    def test_validate_valids(self):
        valid_names = [
            "valid_minimum.yml",
            "valid_everything.yml",
            "integration_additional_volumes.yml",
            "integration_configs.yml",
            "integration_custom_command.yml",
            "integration_env.yml",
            "integration_simple.yml",
            "integration_simple_with_src.yml",
            "integration_src_working_directory.yml",
            "integration_working_directory_absolute.yml",
        ]
        for name in valid_names:
            with self.subTest(name=name):
                service = module.Service.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + name))
                self.init_service(service, service.to_dict())
                self.assertTrue(service.validate())

    def test_validate_invalid_roles(self):
        service = module.Service.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_roles.yml"))
        with self.assertRaisesRegex(SchemaError, "should be instance of 'list'"):
            service.validate()

    def test_validate_invalid_no_image(self):
        service = module.Service.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_no_image.yml"))
        with self.assertRaisesRegex(SchemaError, "Missing key: 'image'"):
            service.validate()

    def test_validate_invalid_logging(self):
        service = module.Service.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_logging.yml"))
        with self.assertRaisesRegex(SchemaError, "should be instance of 'bool'"):
            service.validate()

    def test_validate_invalid_config(self):
        with self.assertRaises(ConfigcrunchError):
            service = module.Service.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_config.yml"))
            service.freeze()
            self.init_service(service, service.doc)

    def test_validate_invalid_additional_volumes(self):
        service = module.Service.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_additional_volumes.yml"))
        with self.assertRaisesRegex(SchemaError, r"Or\('rw', 'ro'\) did not validate"):
            service.validate()

    def test_validate_invalid_ports(self):
        service = module.Service.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_additional_ports.yml"))
        with self.assertRaisesRegex(SchemaError, "should be instance of 'int'"):
            service.validate()

    def test_validate_extra_db_but_no_db_driver(self):
        service = module.Service.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "invalid_db_but_no_db_driver.yml"))
        with self.assertRaisesRegex(
            ConfigcrunchError,
            "If a service has the role 'db' it has to have a valid 'driver' entry with a driver that is available.",
        ):
            service.validate()

    def test_validate_extra_db_driver(self):
        service = module.Service.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "valid_db_driver.yml"))

        with patch_mock_db_driver("riptide.config.document.service.db_driver_for_service.get") as (_, driver):
            service._db_driver = driver
            service.validate()
            driver.validate_service.assert_called_once()

    def test_validate_extra_db_driver_not_found(self):
        service = module.Service.from_yaml(get_fixture_path(FIXTURE_BASE_PATH + "valid_db_driver.yml"))
        self.init_service(service, service.to_dict())
        # not setting _db_driver.
        with self.assertRaisesRegex(
            ConfigcrunchError,
            "If a service has the role 'db' it has to have a valid 'driver' entry with a driver that is available.",
        ):
            service.validate()

    @mock.patch("os.path.exists", side_effect=lambda path: path.startswith("FIRST~DIRNAME"))
    @mock.patch("os.path.dirname", side_effect=lambda path: path + "~DIRNAME")
    def test_init_data_after_merge_config_has_paths_found_at_first(self, dirname_mock: Mock, exists_mock: Mock):
        service = module.Service.from_dict(
            {
                "config": {
                    "one": {"from": "config1/path", "to": "doesnt matter"},
                    "two": {"from": "config2/path2/blub", "to": "doesnt matter2"},
                }
            }
        )
        service.absolute_paths = ["FIRST", "SECOND"]
        service.freeze()
        self.init_service(service, service.doc)

        self.assertEqual(
            {
                "one": {
                    "from": "config1/path",
                    "to": "doesnt matter",
                    "$source": os.path.join("FIRST~DIRNAME", "config1/path"),
                },
                "two": {
                    "from": "config2/path2/blub",
                    "to": "doesnt matter2",
                    "$source": os.path.join("FIRST~DIRNAME", "config2/path2/blub"),
                },
            },
            service["config"],
        )

        dirname_mock.assert_has_calls([call("FIRST"), call("SECOND")])

    @mock.patch("os.path.exists", side_effect=lambda path: path.startswith("SECOND~DIRNAME"))
    @mock.patch("os.path.dirname", side_effect=lambda path: path + "~DIRNAME")
    def test_init_data_after_merge_config_has_paths_found_at_second(self, dirname_mock: Mock, exists_mock: Mock):
        service = module.Service.from_dict(
            {
                "config": {
                    "one": {"from": "config1/path", "to": "doesnt matter"},
                    "two": {"from": "config2/path2/blub", "to": "doesnt matter2"},
                }
            }
        )
        service.absolute_paths = ["FIRST", "SECOND"]
        service.freeze()
        self.init_service(service, service.doc)

        self.assertEqual(
            {
                "one": {
                    "from": "config1/path",
                    "to": "doesnt matter",
                    "$source": os.path.join("SECOND~DIRNAME", "config1/path"),
                },
                "two": {
                    "from": "config2/path2/blub",
                    "to": "doesnt matter2",
                    "$source": os.path.join("SECOND~DIRNAME", "config2/path2/blub"),
                },
            },
            service["config"],
        )

        dirname_mock.assert_has_calls([call("FIRST"), call("SECOND")])

    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("os.path.dirname", side_effect=lambda path: path + "~DIRNAME")
    def test_init_data_after_merge_config_has_paths_not_found(self, dirname_mock: Mock, exist_mock: Mock):
        service = module.Service.from_dict(
            {
                "config": {
                    "one": {"from": "config1/path", "to": "doesnt matter"},
                    "two": {"from": "config2/path2/blub", "to": "doesnt matter2"},
                }
            }
        )
        service.absolute_paths = ["FIRST", "SECOND"]
        service.freeze()
        with self.assertRaisesRegex(ConfigcrunchError, "This probably happens because one of your services"):
            self.init_service(service, service.doc)

    @mock.patch("os.path.exists", return_value=True)
    def test_init_data_after_merge_config_has_project(self, exist_mock: Mock):
        service = module.Service.from_dict(
            {
                "config": {
                    "one": {"from": "config1/path", "to": "doesnt matter"},
                    "two": {"from": "config2/path2/blub", "to": "doesnt matter2"},
                }
            }
        )
        service.parent_doc = ProjectStub.make_project({}, set_parent_to_self=True)
        service.freeze()
        self.init_service(service, service.doc, with_project=True)

        source_path_1 = os.path.join(ProjectStub.FOLDER, "config1/path")
        source_path_2 = os.path.join(ProjectStub.FOLDER, "config2/path2/blub")

        self.assertEqual(
            {
                "one": {
                    "from": "config1/path",
                    "to": "doesnt matter",
                    "$source": source_path_1,
                },
                "two": {
                    "from": "config2/path2/blub",
                    "to": "doesnt matter2",
                    "$source": source_path_2,
                },
            },
            service["config"],
        )

        exist_mock.assert_has_calls(
            [
                call(source_path_1),
                call(source_path_2),
            ],
            any_order=True,
        )

    @mock.patch("os.path.exists", return_value=True)
    def test_init_data_after_merge_config_has_no_path_no_project(self, exist_mock: Mock):
        service = module.Service.from_dict(
            {
                "config": {
                    "one": {"from": "config1/path", "to": "doesnt matter"},
                    "two": {"from": "config2/path2/blub", "to": "doesnt matter2"},
                }
            }
        )
        service.freeze()
        self.init_service(service, service.doc)

        # Fallback is os.getcwd()
        self.assertEqual(
            {
                "one": {
                    "from": "config1/path",
                    "to": "doesnt matter",
                    "$source": os.path.join(os.getcwd(), "config1/path"),
                },
                "two": {
                    "from": "config2/path2/blub",
                    "to": "doesnt matter2",
                    "$source": os.path.join(os.getcwd(), "config2/path2/blub"),
                },
            },
            service["config"],
        )

        exist_mock.assert_has_calls(
            [call(os.path.join(os.getcwd(), "config1/path")), call(os.path.join(os.getcwd(), "config2/path2/blub"))],
            any_order=True,
        )

    def test_init_data_after_merge_config_illegal_config_from_dot(self):
        doc = {"config": {"one": {"from": ".PATH", "to": "doesnt matter"}}}

        service = module.Service(doc)
        service.absolute_paths = ["PATH"]
        service.freeze()
        with self.assertRaises(ConfigcrunchError):
            self.init_service(service, service.doc)

    def test_init_data_after_merge_config_illegal_config_from_os_sep(self):
        doc = {"config": {"one": {"from": os.sep + "PATH", "to": "doesnt matter"}}}

        service = module.Service(doc)
        service.absolute_paths = ["PATH"]
        service.freeze()
        with self.assertRaises(ConfigcrunchError):
            self.init_service(service, service.doc)

    def test_init_data_after_merge_config_invalid_entry(self):
        # Invalid entries should be skipped, the validation will
        # filter them out.
        doc = {"config": {"one": {"to": "doesnt matter"}}}

        service = module.Service(doc)
        service.absolute_paths = ["PATH"]
        service.freeze()
        self.init_service(service, service.doc)
        self.assertDictEqual(doc["config"], service["config"])

    def test_initialize_data_after_merge_set_defaults(self):
        service = module.Service.from_dict({})
        service.freeze()
        self.init_service(service, service.doc)
        self.assertEqual(
            {
                "run_as_current_user": True,
                "dont_create_user": False,
                "ignore_original_entrypoint": False,
                "pre_start": [],
                "post_start": [],
                "roles": [],
                "working_directory": ".",
                "additional_subdomains": [],
                "run_post_start_as_current_user": True,
                "run_pre_start_as_current_user": True,
                "read_env_file": True,
            },
            service.doc,
        )

    def test_initialize_data_after_merge_values_already_set(self):
        service = module.Service.from_dict(
            {
                "run_as_current_user": "SET",
                "dont_create_user": "SET",
                "ignore_original_entrypoint": "SET",
                "pre_start": "SET",
                "post_start": "SET",
                "roles": "SET",
                "working_directory": "SET",
                "additional_subdomains": "SET",
                "run_post_start_as_current_user": "SET",
                "run_pre_start_as_current_user": "SET",
                "read_env_file": "SET",
            }
        )
        service.freeze()
        self.init_service(service, service.doc)
        self.assertEqual(
            {
                "run_as_current_user": "SET",
                "dont_create_user": "SET",
                "ignore_original_entrypoint": "SET",
                "pre_start": "SET",
                "post_start": "SET",
                "roles": "SET",
                "working_directory": "SET",
                "additional_subdomains": "SET",
                "run_post_start_as_current_user": "SET",
                "run_pre_start_as_current_user": "SET",
                "read_env_file": "SET",
            },
            service.doc,
        )

    def test_initialize_data_after_merge_db_driver_setup(self):
        doc = {"roles": ["db"], "additional_ports": {"one": 1, "two": 2, "three": 3}}
        service = module.Service(doc)
        with patch_mock_db_driver("riptide.config.document.service.db_driver_for_service.get") as (get, driver):
            driver.collect_additional_ports = MagicMock(return_value={"four": 4, "five": 5, "three": 6})
            service.freeze()
            self.init_service(service, service.doc)
            get.assert_called_once_with(service.doc, service)
            self.assertEqual({"one": 1, "two": 2, "four": 4, "five": 5, "three": 3}, service.doc["additional_ports"])

    @mock.patch("riptide.config.document.service.cppath.normalize", return_value="NORMALIZED")
    def test_initialize_data_after_variables(self, normalize_mock: Mock):
        service = module.Service.from_dict(
            {
                "additional_volumes": {
                    "one": {
                        "host": "TEST1",
                    },
                    "two": {"host": "TEST2", "mode": "rw"},
                },
                "config": {
                    "three": {"$source": "TEST3"},
                    "four": {
                        "$source": "TEST4",
                        "to": "/to",
                        "from": "/from",
                    },
                },
            }
        )
        expected = {
            "additional_volumes": {
                "one": {
                    "host": "NORMALIZED",
                },
                "two": {"host": "NORMALIZED", "mode": "rw"},
            },
            "config": {
                "three": {"$source": "NORMALIZED"},
                "four": {
                    "$source": "NORMALIZED",
                    "to": "/to",
                    "from": "/from",
                },
            },
        }
        service.freeze()
        service._initialize_data_after_variables(service.doc)
        self.assertEqual(
            4, normalize_mock.call_count, "cppath.normalize has to be called once for each volume and each config"
        )

        self.assertEqual(expected, service.doc)

    @mock.patch("os.makedirs")
    @mock.patch(
        "riptide.config.document.service.get_additional_port", side_effect=lambda p, s, host_start: host_start + 10
    )
    def test_before_start(self, get_additional_port_mock: Mock, makedirs_mock: Mock):
        project_stub = ProjectStub.make_project({"src": "SRC"}, set_parent_to_self=True)
        service = module.Service.from_dict(
            {
                "working_directory": "WORKDIR",
                "additional_ports": {
                    "one": {"container": 1, "host_start": 2},
                    "two": {"container": 2, "host_start": 3},
                    "three": {"container": 3, "host_start": 4},
                },
            }
        )
        service.parent_doc = project_stub

        project_stub.freeze()
        service.freeze()
        service.before_start()

        self.assertEqual({1: 12, 2: 13, 3: 14}, service._loaded_port_mappings)

        get_additional_port_mock.assert_has_calls(
            [call(project_stub, service, 2), call(project_stub, service, 3), call(project_stub, service, 4)],
            any_order=True,
        )

        # Assert creation of working directory
        makedirs_mock.assert_called_with(os.path.join(ProjectStub.FOLDER, "SRC", "WORKDIR"), exist_ok=True)

    @mock.patch("os.makedirs")
    def test_before_start_absolute_workdir(self, makedirs_mock: Mock):
        project_stub = ProjectStub.make_project({"src": "SRC"}, set_parent_to_self=True)
        service = module.Service.from_dict({"working_directory": "/WORKDIR"})
        service.parent_doc = project_stub

        service.freeze()
        project_stub.freeze()

        service.before_start()

        # Assert NO creation of working directory
        makedirs_mock.assert_not_called()

    @mock.patch("os.makedirs")
    def test_before_start_absolute_workdir_no_workdir(self, makedirs_mock: Mock):
        project_stub = ProjectStub.make_project({"src": "SRC"}, set_parent_to_self=True)
        service = module.Service.from_dict({})
        service.parent_doc = project_stub

        service.freeze()
        project_stub.freeze()

        service.before_start()

        # Assert NO creation of working directory
        makedirs_mock.assert_not_called()

    def test_get_project(self):
        service = module.Service.from_dict({})
        project = ProjectStub.make_project({}, set_parent_to_self=True)
        service.parent_doc = project
        service.freeze()
        self.assertEqual(project, service.get_project())

    def test_get_project_no_parent(self):
        service = module.Service.from_dict({})
        with self.assertRaises(IndexError):
            service.get_project()

    @mock.patch("riptide.config.document.service.create_logging_path")
    @mock.patch(
        "riptide.config.document.service.get_command_logging_container_path",
        side_effect=lambda name: name + "~PROCESSED3",
    )
    @mock.patch(
        "riptide.config.document.service.get_logging_path_for", side_effect=lambda _, name: name + "~PROCESSED2"
    )
    @mock.patch("os.makedirs")
    @mock.patch("riptide.config.document.service.process_config", side_effect=process_config_stub)
    @mock.patch(
        "riptide.config.document.service.process_additional_volumes", return_value={STUB_PAV__KEY: STUB_PAV__VAL}
    )
    def test_collect_volumes(
        self,
        process_additional_volumes_mock: Mock,
        process_config_mock: Mock,
        makedirs_mock: Mock,
        get_logging_path_for_mock: Mock,
        get_command_logging_container_path_mock: Mock,
        create_logging_path_mock: Mock,
    ):
        config1 = {"to": "/TO_1", "from": "/FROM_1"}
        config2 = {"to": "/TO_2", "from": "/FROM_2"}
        config3 = {"to": "TO_3_RELATIVE", "from": "/FROM_3"}
        service = module.Service.from_dict(
            {
                "roles": ["src"],
                "config": {"config1": config1, "config2": config2, "config3": config3},
                "logging": {
                    "stdout": True,
                    "stderr": True,
                    "paths": {"one": "one_path", "two": "two_path", "three": "three_path"},
                    "commands": {"four": "not used here"},
                },
                "additional_volumes": {
                    "one": {"host": "~/hometest", "container": "/vol1", "mode": "rw"},
                    "2": {"host": "./reltest1", "container": "/vol2", "mode": "rw"},
                    "three": {"host": "reltest2", "container": "/vol3", "mode": "rw"},
                    "FOUR": {"host": "reltestc", "container": "reltest_container", "mode": "rw"},
                    "faive": {"host": "/absolute_with_ro", "container": "/vol4", "mode": "ro"},
                    "xis": {"host": "/absolute_no_mode", "container": "/vol5"},
                },
            }
        )
        expected = {
            # SRC
            ProjectStub.SRC_FOLDER: {"bind": CONTAINER_SRC_PATH, "mode": "rw"},
            # CONFIG
            "config1~/FROM_1~~True": {"bind": "/TO_1", "mode": "STUB"},
            "config2~/FROM_2~~True": {"bind": "/TO_2", "mode": "STUB"},
            "config3~/FROM_3~~True": {"bind": "/src/TO_3_RELATIVE", "mode": "STUB"},
            # LOGGING
            "stdout~PROCESSED2": {"bind": module.LOGGING_CONTAINER_STDOUT, "mode": "rw"},
            "stderr~PROCESSED2": {"bind": module.LOGGING_CONTAINER_STDERR, "mode": "rw"},
            "one~PROCESSED2": {"bind": "one_path", "mode": "rw"},
            "two~PROCESSED2": {"bind": "two_path", "mode": "rw"},
            "three~PROCESSED2": {"bind": "three_path", "mode": "rw"},
            "four~PROCESSED2": {"bind": "four~PROCESSED3", "mode": "rw"},
            # DB DRIVER
            "FROM_DB_DRIVER": "VALUE",
            # ADDITIONAL VOLUMES
            # process_additional_volumes has to be called
            STUB_PAV__KEY: STUB_PAV__VAL,
        }

        service.parent_doc = ProjectStub.make_project({}, set_parent_to_self=True)

        ## DB DRIVER SETUP
        with patch_mock_db_driver("riptide.config.document.service.db_driver_for_service.get") as (_, driver):
            service._db_driver = driver
            driver.collect_volumes.return_value = {"FROM_DB_DRIVER": "VALUE"}

        service.freeze()
        ## OVERALL ASSERTIONS
        actual = service.collect_volumes()
        self.assertEqual(expected, actual)
        self.assertIsInstance(actual, OrderedDict)

        ## LOGGING ASSERTIONS
        get_logging_path_for_mock.assert_has_calls(
            [
                call(service, "stdout"),
                call(service, "stderr"),
                call(service, "one"),
                call(service, "two"),
                call(service, "three"),
                call(service, "four"),
            ],
            any_order=True,
        )
        get_command_logging_container_path_mock.assert_has_calls(
            [
                call("four"),
            ],
            any_order=True,
        )
        create_logging_path_mock.assert_called_once()

        ## ADDITIONAL VOLUMES ASSERTIONS
        process_additional_volumes_mock.assert_called_with(
            list(service["additional_volumes"].values()), ProjectStub.FOLDER
        )

        ## DB DRIVER ASSERTIONS
        makedirs_mock.assert_has_calls(
            [
                # DB DRIVER
                call("FROM_DB_DRIVER", exist_ok=True)
            ],
            any_order=True,
        )

    def test_collect_volumes_no_src(self):
        service = module.Service.from_dict({"roles": ["something"]})
        expected: dict[str, str] = {}

        service.parent_doc = ProjectStub.make_project({}, set_parent_to_self=True)
        self.init_service(service, service.to_dict())
        service.freeze()

        ## OVERALL ASSERTIONS
        self.assertEqual(expected, service.collect_volumes())

    @mock.patch("riptide.config.document.service.create_logging_path")
    @mock.patch(
        "riptide.config.document.service.get_logging_path_for", side_effect=lambda _, name: name + "~PROCESSED2"
    )
    def test_collect_volumes_only_stdere(self, get_logging_path_for_mock: Mock, create_logging_path_mock: Mock):
        service = module.Service({"roles": ["something"], "logging": {"stderr": True}})
        expected = {"stderr~PROCESSED2": {"bind": module.LOGGING_CONTAINER_STDERR, "mode": "rw"}}

        service.parent_doc = ProjectStub.make_project({}, set_parent_to_self=True)
        self.init_service(service, service.to_dict())
        service.freeze()

        ## OVERALL ASSERTIONS
        self.assertEqual(expected, service.collect_volumes())

        get_logging_path_for_mock.assert_called_once_with(service, "stderr")
        create_logging_path_mock.assert_called_once()

    def test_collect_environment(self):
        service = module.Service.from_dict({"environment": {"key1": "value1", "key2": "value2"}})

        with patch_mock_db_driver("riptide.config.document.service.db_driver_for_service.get") as (_, driver):
            service._db_driver = driver
            driver.collect_environment.return_value = {"FROM_DB_DRIVER": "VALUE"}

        # TODO: Test reading from env file
        service.parent_doc = ProjectStub.make_project({"env_files": []}, set_parent_to_self=True)
        service.freeze()
        service.get_project().freeze()

        self.assertEqual({"key1": "value1", "key2": "value2", "FROM_DB_DRIVER": "VALUE"}, service.collect_environment())

    def test_collect_ports(self):
        service = module.Service.from_dict({})

        service._loaded_port_mappings = {1: 1, 3: 3, 4: 4}

        self.assertEqual({1: 1, 3: 3, 4: 4}, service.collect_ports())

    @mock.patch("riptide.config.document.service.get_project_meta_folder", side_effect=lambda name: name + "~PROCESSED")
    def test_volume_path(self, get_project_meta_folder_mock: Mock):
        service = module.Service.from_dict({"$name": "TEST"})
        service.parent_doc = ProjectStub.make_project({}, set_parent_to_self=True)

        self.assertEqual(os.path.join(ProjectStub.FOLDER + "~PROCESSED", "data", "TEST"), service.volume_path())

    def test_get_working_directory_no_wd_set_and_src_set(self):
        service = module.Service.from_dict({"roles": ["src"]})

        self.assertEqual(CONTAINER_SRC_PATH, service.get_working_directory())

    def test_get_working_directory_relative_wd_set_and_src_set(self):
        service = module.Service.from_dict({"working_directory": "relative_path/in/test", "roles": ["src"]})

        self.assertEqual(CONTAINER_SRC_PATH + "/relative_path/in/test", service.get_working_directory())

    def test_get_working_directory_absolute_wd_set_and_src_set(self):
        service = module.Service.from_dict({"working_directory": "/path/in/test", "roles": ["?"]})

        self.assertEqual("/path/in/test", service.get_working_directory())

    def test_get_working_directory_no_wd_set_and_src_not_set(self):
        service = module.Service.from_dict({"roles": ["?"]})

        self.assertEqual(None, service.get_working_directory())

    def test_get_working_directory_relative_wd_set_and_src_not_set(self):
        service = module.Service.from_dict({"working_directory": "relative_path/in/test", "roles": ["?"]})

        self.assertEqual(None, service.get_working_directory())

    def test_get_working_directory_absolute_wd_set_and_src_not_set(self):
        service = module.Service.from_dict({"working_directory": "/path/in/test", "roles": ["?"]})

        self.assertEqual("/path/in/test", service.get_working_directory())

    def test_domain_not_main(self):
        system = YamlConfigDocumentStub.make(DocumentClass.Config, {"proxy": {"url": "TEST-URL"}})
        project = ProjectStub.make_project({"name": "TEST-PROJECT"}, parent=system)
        app = YamlConfigDocumentStub.make(DocumentClass.App, {}, parent=project)
        service = module.Service.from_dict({"$name": "TEST-SERVICE", "roles": ["?"]})
        service.parent_doc = app

        self.assertEqual("TEST-PROJECT--TEST-SERVICE.TEST-URL", service.domain())

    def test_domain_main(self):
        system = YamlConfigDocumentStub.make(DocumentClass.Config, {"proxy": {"url": "TEST-URL"}})
        project = ProjectStub.make_project({"name": "TEST-PROJECT"}, parent=system)
        app = YamlConfigDocumentStub.make(DocumentClass.App, {}, parent=project)
        service = module.Service.from_dict({"$name": "TEST-SERVICE", "roles": ["main"]})

        service.parent_doc = app

        service.freeze()
        project.freeze()

        service.before_start()

        self.assertEqual("TEST-PROJECT.TEST-URL", service.domain())

    def test_additional_domains_not_main(self):
        system = YamlConfigDocumentStub.make(DocumentClass.Config, {"proxy": {"url": "TEST-URL"}})
        project = ProjectStub.make_project({"name": "TEST-PROJECT"}, parent=system)
        app = YamlConfigDocumentStub.make(DocumentClass.App, {}, parent=project)
        service = module.Service.from_dict(
            {"$name": "TEST-SERVICE", "roles": ["?"], "additional_subdomains": ["first", "second"]}
        )
        service.parent_doc = app

        self.assertEqual("TEST-PROJECT--TEST-SERVICE.TEST-URL", service.domain())
        result = service.additional_domains()
        self.assertEqual(2, len(result))
        self.assertTrue("first" in result)
        self.assertEqual("first.TEST-PROJECT--TEST-SERVICE.TEST-URL", result["first"])
        self.assertTrue("second" in result)
        self.assertEqual("second.TEST-PROJECT--TEST-SERVICE.TEST-URL", result["second"])

    def test_additional_domains_main(self):
        system = YamlConfigDocumentStub.make(DocumentClass.Config, {"proxy": {"url": "TEST-URL"}})
        project = ProjectStub.make_project({"name": "TEST-PROJECT"}, parent=system)
        app = YamlConfigDocumentStub.make(DocumentClass.App, {}, parent=project)
        service = module.Service.from_dict(
            {"$name": "TEST-SERVICE", "roles": ["main"], "additional_subdomains": ["first", "second"]}
        )
        service.parent_doc = app

        self.assertEqual("TEST-PROJECT.TEST-URL", service.domain())
        result = service.additional_domains()
        self.assertEqual(2, len(result))
        self.assertTrue("first" in result)
        self.assertEqual("first.TEST-PROJECT.TEST-URL", result["first"])
        self.assertTrue("second" in result)
        self.assertEqual("second.TEST-PROJECT.TEST-URL", result["second"])

    @mock.patch("riptide.config.document.common_service_command.getuid", return_value=1234)
    def test_os_user(self, getuid_mock: Mock):
        service = module.Service.from_dict({})
        self.assertEqual("1234", service.os_user())
        getuid_mock.assert_called_once()

    @mock.patch("riptide.config.document.common_service_command.getgid", return_value=1234)
    def test_os_group(self, getgid_mock: Mock):
        service = module.Service.from_dict({})
        self.assertEqual("1234", service.os_group())
        getgid_mock.assert_called_once()

    def test_host_address(self):
        service = module.Service.from_dict({})
        self.assertEqual(RIPTIDE_HOST_HOSTNAME, service.host_address())

    def test_home_path(self):
        service = module.Service.from_dict({})
        self.assertEqual(CONTAINER_HOME_PATH, service.home_path())

    def init_service(self, service: module.Service, doc: dict, with_project: bool = False):
        if with_project:
            # XXX: Not ideal, see comment at CURRENTLY_LOADING_PROJECT_PATH
            LOADER_MODULE.CURRENTLY_LOADING_PROJECT_PATH = os.path.join(ProjectStub.FOLDER, "riptide.yml")
        try:
            service._initialize_data_after_merge(doc)
        finally:
            LOADER_MODULE.CURRENTLY_LOADING_PROJECT_PATH = None
