import os
import unittest
from unittest import mock

from unittest.mock import Mock, MagicMock, call

from schema import SchemaError

import riptide.config.document.service as module
from configcrunch import ConfigcrunchError
from configcrunch.tests.test_utils import YamlConfigDocumentStub
from riptide.config.files import CONTAINER_SRC_PATH, CONTAINER_HOME_PATH
from riptide.engine.abstract import RIPTIDE_HOST_HOSTNAME
from riptide.tests.helpers import patch_mock_db_driver, get_fixture_path
from riptide.tests.stubs import ProjectStub


FIXTURE_BASE_PATH = 'service' + os.sep

class ServiceTestCase(unittest.TestCase):

    def test_header(self):
        service = module.Service({}, dont_call_init_data=True)
        self.assertEqual(module.HEADER, service.header())

    def test_validate_valids(self):
        valid_names = ['valid_minimum.yml', 'valid_everything.yml']
        for name in valid_names:
            with self.subTest(name=name):
                service = module.Service.from_yaml(get_fixture_path(
                    FIXTURE_BASE_PATH + name
                ))
                self.assertTrue(service.validate())

    def test_validate_invalid_roles(self):
        service = module.Service.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_roles.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "should be instance of 'list'"):
            service.validate()

    def test_validate_invalid_no_image(self):
        service = module.Service.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_no_image.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing keys: 'image'"):
            service.validate()

    def test_validate_invalid_logging(self):
        service = module.Service.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_logging.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "should be instance of 'bool'"):
            service.validate()

    def test_validate_invalid_config(self):
        service = module.Service.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_config.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Missing keys: 'to'"):
            service.validate()

    def test_validate_invalid_additional_volumes(self):
        service = module.Service.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_additional_volumes.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "Or\('rw', 'ro'\) did not validate"):
            service.validate()

    def test_validate_invalid_ports(self):
        service = module.Service.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_additional_ports.yml'
        ))
        with self.assertRaisesRegex(SchemaError, "should be instance of 'int'"):
            service.validate()

    def test_validate_extra_db_but_no_db_driver(self):
        service = module.Service.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'invalid_db_but_no_db_driver.yml'
        ))
        with self.assertRaisesRegex(ConfigcrunchError,
                                    "If a service has the role 'db' it has to have "
                                    "a valid 'driver' entry with a driver that "
                                    "is available."):
            service.validate()

    def test_validate_extra_db_driver(self):
        service = module.Service.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'valid_db_driver.yml'
        ))

        with patch_mock_db_driver(
                'riptide.config.document.service.db_driver_for_service.get'
        ) as (_, driver):
            service._db_driver = driver
            service.validate()
            driver.validate_service.assert_called_once()

    def test_validate_extra_db_driver_not_found(self):
        service = module.Service.from_yaml(get_fixture_path(
            FIXTURE_BASE_PATH + 'valid_db_driver.yml'
        ))
        # not setting _db_driver.
        with self.assertRaisesRegex(ConfigcrunchError,
                                    "If a service has the role 'db' it has to have "
                                    "a valid 'driver' entry with a driver that "
                                    "is available."):
            service.validate()

    @mock.patch("os.path.dirname", return_value='DIRNAME')
    def test_initialize_data_before_merge_has_path(self, dirname_mock: Mock):
        # Tested via calling the constrcutor with dont_call_init_data=False (default)
        service = module.Service({
            "config": [
                {
                    "from": "config1/path",
                    "to": "doesnt matter"
                },
                {
                    "from": "config2/path2/blub",
                    "to": "doesnt matter2"
                }
            ]
        }, absolute_path='PATH')

        self.assertEqual([
            {
                "from": "config1/path",
                "to": "doesnt matter",
                "$source": os.path.join("DIRNAME", "config1/path")
            },
            {
                "from": "config2/path2/blub",
                "to": "doesnt matter2",
                "$source": os.path.join("DIRNAME", "config2/path2/blub")
            }
        ], service['config'])

        dirname_mock.assert_called_once_with('PATH')

    def test_initialize_data_before_merge_has_project(self):
        service = module.Service({
            "config": [
                {
                    "from": "config1/path",
                    "to": "doesnt matter"
                },
                {
                    "from": "config2/path2/blub",
                    "to": "doesnt matter2"
                }
            ]
        }, parent=ProjectStub({}, set_parent_to_self=True))

        self.assertEqual([
            {
                "from": "config1/path",
                "to": "doesnt matter",
                "$source": os.path.join(ProjectStub.FOLDER, "config1/path")
            },
            {
                "from": "config2/path2/blub",
                "to": "doesnt matter2",
                "$source": os.path.join(ProjectStub.FOLDER, "config2/path2/blub")
            }
        ], service['config'])

    def test_initialize_data_before_merge_has_no_path_no_project(self):
        service = module.Service({
            "config": [
                {
                    "from": "config1/path",
                    "to": "doesnt matter"
                },
                {
                    "from": "config2/path2/blub",
                    "to": "doesnt matter2"
                }
            ]
        })

        # Fallback is os.getcwd()
        self.assertEqual([
            {
                "from": "config1/path",
                "to": "doesnt matter",
                "$source": os.path.join(os.getcwd(), "config1/path")
            },
            {
                "from": "config2/path2/blub",
                "to": "doesnt matter2",
                "$source": os.path.join(os.getcwd(), "config2/path2/blub")
            }
        ], service['config'])

    def test_initialize_data_before_merge_illegal_config_from_dot(self):
        doc = {
            "config": [{
                "from": ".PATH",
                "to": "doesnt matter"
            }]
        }

        with self.assertRaises(ConfigcrunchError):
            module.Service(doc, absolute_path='PATH')

    def test_initialize_data_before_merge_illegal_config_from_os_sep(self):
        doc = {
            "config": [{
                "from": os.sep + "PATH",
                "to": "doesnt matter"
            }]
        }

        with self.assertRaises(ConfigcrunchError):
            module.Service(doc, absolute_path='PATH')

    def test_initialize_data_after_merge_set_defaults(self):
        service = module.Service({}, dont_call_init_data=True)
        service._initialize_data_after_merge()
        self.assertEqual({
            "run_as_root": False,
            "dont_create_user": False,
            "pre_start": [],
            "post_start": [],
            "roles": [],
            "additional_ports": []
        }, service.doc)

    def test_initialize_data_after_merge_values_already_set(self):
        service = module.Service({
            "run_as_root": 'SET',
            "dont_create_user": 'SET',
            "pre_start": 'SET',
            "post_start": 'SET',
            "roles": 'SET',
            "additional_ports": 'SET'
        }, dont_call_init_data=True)
        service._initialize_data_after_merge()
        self.assertEqual({
            "run_as_root": 'SET',
            "dont_create_user": 'SET',
            "pre_start": 'SET',
            "post_start": 'SET',
            "roles": 'SET',
            "additional_ports": 'SET'
        }, service.doc)

    def test_initialize_data_after_merge_db_driver_setup(self):
        doc = {
            "roles": ["db"],
            "additional_ports": [1, 2, 3]
        }
        service = module.Service(doc, dont_call_init_data=True)
        with patch_mock_db_driver(
                'riptide.config.document.service.db_driver_for_service.get'
        ) as (get, driver):
            driver.collect_additional_ports = MagicMock(return_value=[4, 5, 6])
            service._initialize_data_after_merge()
            get.assert_called_once_with(service)
            self.assertEqual([1, 2, 3, 4, 5, 6], service.doc["additional_ports"])

    @mock.patch('riptide.config.document.service.cppath.normalize', return_value='NORMALIZED')
    def test_initialize_data_after_variables(self, normalize_mock: Mock):
        service = module.Service({
            "additional_volumes": [
                {
                    "host": "TEST1",
                },
                {
                    "host": "TEST2",
                    "mode": "rw"
                }
            ],
            "config": [
                {
                    "$source": "TEST3"
                },
                {
                    "$source": "TEST4",
                    "to": "/to",
                    "from": "/from",
                }
            ]
        }, dont_call_init_data=True)
        expected = {
            "additional_volumes": [
                {
                    "host": "NORMALIZED",
                },
                {
                    "host": "NORMALIZED",
                    "mode": "rw"
                }
            ],
            "config": [
                {
                    "$source": "NORMALIZED"
                },
                {
                    "$source": "NORMALIZED",
                    "to": "/to",
                    "from": "/from",
                }
            ]
        }
        service._initialize_data_after_variables()
        self.assertEqual(4, normalize_mock.call_count,
                         "cppath.normalize has to be called once for each volume and each config")

        self.assertEqual(expected, service.doc)

    @mock.patch("riptide.config.document.service.get_additional_port",
                side_effect=lambda p, s, host_start: host_start + 10)
    def test_before_start(self, get_additional_port_mock: Mock):
        project_stub = ProjectStub({}, set_parent_to_self=True)
        service = module.Service({
            "additional_ports": [
                {
                    "container": 1,
                    "host_start": 2
                },
                {
                    "container": 2,
                    "host_start": 3
                },
                {
                    "container": 3,
                    "host_start": 4
                },
            ]
        }, dont_call_init_data=True, parent=project_stub)

        service.before_start()

        self.assertEqual({
            1: 12,
            2: 13,
            3: 14
        }, service._loaded_port_mappings)

        get_additional_port_mock.assert_has_calls([
            call(project_stub, service, 2),
            call(project_stub, service, 3),
            call(project_stub, service, 4)
        ], any_order=True)

    def test_get_project(self):
        service = module.Service({}, dont_call_init_data=True)
        project = ProjectStub({}, set_parent_to_self=True)
        service.parent_doc = project
        self.assertEqual(project, service.get_project())

    def test_get_project_no_parent(self):
        service = module.Service({}, dont_call_init_data=True)
        with self.assertRaises(IndexError):
            service.get_project()

    @mock.patch("riptide.config.document.service.create_logging_path")
    @mock.patch("riptide.config.document.service.get_command_logging_container_path",
                side_effect=lambda name: name + "~PROCESSED3")
    @mock.patch("riptide.config.document.service.get_logging_path_for",
                side_effect=lambda _, name: name + "~PROCESSED2")
    @mock.patch("os.makedirs")
    @mock.patch("riptide.config.document.service.process_config",
                side_effect=lambda config, _: config["from"] + "~PROCESSED")
    @mock.patch("os.path.expanduser", return_value=os.sep + 'HOME')
    def test_collect_volumes(self,
                             expanduser_mock: Mock, process_config_mock: Mock, makedirs_mock: Mock,
                             get_logging_path_for_mock: Mock, get_command_logging_container_path_mock: Mock,
                             create_logging_path_mock: Mock
                             ):
        config1 = {'to': '/TO_1', 'from': '/FROM_1'}
        config2 = {'to': '/TO_2', 'from': '/FROM_2'}
        config3 = {'to': '/TO_3', 'from': '/FROM_3'}
        service = module.Service({
            "roles": ["src"],
            "config": [
                config1, config2, config3
            ],
            "logging": {
                "stdout": True,
                "stderr": True,
                "paths": {
                    "one": "one_path",
                    "two": "two_path",
                    "three": "three_path"
                },
                "commands": {
                    "four": "not used here"
                }
            },
            "additional_volumes": [
                {
                    "host": "~/hometest",
                    "container": "/vol1",
                    "mode": "rw"
                },
                {
                    "host": "./reltest1",
                    "container": "/vol2",
                    "mode": "rw"
                },
                {
                    "host": "reltest2",
                    "container": "/vol3",
                    "mode": "rw"
                },
                {
                    "host": "/absolute_with_ro",
                    "container": "/vol4",
                    "mode": "ro"
                },
                {
                    "host": "/absolute_no_mode",
                    "container": "/vol5"
                }
            ]
        }, dont_call_init_data=True)
        expected = {
            # SRC
            ProjectStub.SRC_FOLDER:                         {'bind': CONTAINER_SRC_PATH, 'mode': 'rw'},
            # CONFIG
            '/FROM_1~PROCESSED':                            {'bind': '/TO_1', 'mode': 'rw'},
            '/FROM_2~PROCESSED':                            {'bind': '/TO_2', 'mode': 'rw'},
            '/FROM_3~PROCESSED':                            {'bind': '/TO_3', 'mode': 'rw'},
            # LOGGING
            'stdout~PROCESSED2':                            {'bind': module.LOGGING_CONTAINER_STDOUT, 'mode': 'rw'},
            'stderr~PROCESSED2':                            {'bind': module.LOGGING_CONTAINER_STDERR, 'mode': 'rw'},
            'one~PROCESSED2':                               {'bind': 'one_path', 'mode': 'rw'},
            'two~PROCESSED2':                               {'bind': 'two_path', 'mode': 'rw'},
            'three~PROCESSED2':                             {'bind': 'three_path', 'mode': 'rw'},
            'four~PROCESSED2':                              {'bind': 'four~PROCESSED3', 'mode': 'rw'},
            # DB DRIVER
            'FROM_DB_DRIVER':                               'VALUE',
            # ADDITIONAL VOLUMES
            os.path.join(os.sep + 'HOME', 'hometest'):      {'bind': '/vol1', 'mode': 'rw'},
            os.path.join(ProjectStub.FOLDER, './reltest1'): {'bind': '/vol2', 'mode': 'rw'},
            os.path.join(ProjectStub.FOLDER, 'reltest2'):   {'bind': '/vol3', 'mode': 'rw'},
            '/absolute_with_ro':                            {'bind': '/vol4', 'mode': 'ro'},
            '/absolute_no_mode':                            {'bind': '/vol5', 'mode': 'rw'}
        }

        service.parent_doc = ProjectStub({}, set_parent_to_self=True)

        ## DB DRIVER SETUP
        with patch_mock_db_driver(
                'riptide.config.document.service.db_driver_for_service.get'
        ) as (_, driver):
            service._db_driver = driver
            driver.collect_volumes.return_value = {'FROM_DB_DRIVER': 'VALUE'}

        ## OVERALL ASSERTIONS
        self.assertEqual(expected, service.collect_volumes())

        ## CONFIG ASSERTIONS
        process_config_mock.assert_has_calls([
            call(config1, service),
            call(config2, service),
            call(config3, service),
        ], any_order=True)

        ## LOGGING ASSERTIONS
        get_logging_path_for_mock.assert_has_calls([
            call(service, "stdout"),
            call(service, "stderr"),
            call(service, "one"),
            call(service, "two"),
            call(service, "three"),
            call(service, "four"),
        ], any_order=True)
        get_command_logging_container_path_mock.assert_has_calls([
            call("four"),
        ], any_order=True)
        create_logging_path_mock.assert_called_once()

        ## ADDITIONAL VOLUMES ASSERTIONS
        # First volume had ~ in it:
        expanduser_mock.assert_called_once_with('~')

        ## ADDITIONAL VOLUMES AND DB DRIVER ASSERTIONS
        makedirs_mock.assert_has_calls([
            # ADDITIONAL VOLUMES
            call(os.path.join(os.sep + 'HOME', 'hometest'), exist_ok=True),
            call(os.path.join(ProjectStub.FOLDER, './reltest1'), exist_ok=True),
            call(os.path.join('/absolute_with_ro'), exist_ok=True),
            call(os.path.join('/absolute_no_mode'), exist_ok=True),
            # DB DRIVER
            call('FROM_DB_DRIVER', exist_ok=True)
        ], any_order=True)

    def test_collect_volumes_no_src(self):
        config1 = {'to': '/TO_1', 'from': '/FROM_1'}
        config2 = {'to': '/TO_2', 'from': '/FROM_2'}
        config3 = {'to': '/TO_2', 'from': '/FROM_3'}
        service = module.Service({"roles": ["something"]}, dont_call_init_data=True)
        expected = {}

        service.parent_doc = ProjectStub({}, set_parent_to_self=True)

        ## OVERALL ASSERTIONS
        self.assertEqual(expected, service.collect_volumes())

    @mock.patch("riptide.config.document.service.create_logging_path")
    @mock.patch("riptide.config.document.service.get_logging_path_for",
                side_effect=lambda _, name: name + "~PROCESSED2")
    def test_collect_volumes_only_stdere(self, get_logging_path_for_mock: Mock, create_logging_path_mock: Mock):
        config1 = {'to': '/TO_1', 'from': '/FROM_1'}
        config2 = {'to': '/TO_2', 'from': '/FROM_2'}
        config3 = {'to': '/TO_2', 'from': '/FROM_3'}
        service = module.Service(
            {"roles": ["something"], "logging": {"stderr": True}}, dont_call_init_data=True)
        expected = {
            'stderr~PROCESSED2':                            {'bind': module.LOGGING_CONTAINER_STDERR, 'mode': 'rw'}
        }

        service.parent_doc = ProjectStub({}, set_parent_to_self=True)

        ## OVERALL ASSERTIONS
        self.assertEqual(expected, service.collect_volumes())

        get_logging_path_for_mock.assert_called_once_with(service, 'stderr')
        create_logging_path_mock.assert_called_once()

    def test_collect_environment(self):
        service = module.Service({
                "environment": {
                    "key1": "value1",
                    "key2": "value2"
                }
         }, dont_call_init_data=True)

        with patch_mock_db_driver(
                'riptide.config.document.service.db_driver_for_service.get'
        ) as (_, driver):
            service._db_driver = driver
            driver.collect_environment.return_value = {'FROM_DB_DRIVER': 'VALUE'}

        self.assertEqual({
            "key1": "value1",
            "key2": "value2",
            "FROM_DB_DRIVER": "VALUE"
        }, service.collect_environment())

    def test_collect_ports(self):
        service = module.Service({}, dont_call_init_data=True)

        service._loaded_port_mappings = [1, 3, 4]

        self.assertEqual([1, 3, 4], service.collect_ports())

    @mock.patch("riptide.config.document.service.get_project_meta_folder",
                side_effect=lambda name: name + '~PROCESSED')
    def test_volume_path(self, get_project_meta_folder_mock: Mock):
        service = module.Service({'$name': 'TEST'},
                                 dont_call_init_data=True,
                                 parent=ProjectStub({}, set_parent_to_self=True))

        self.assertEqual(os.path.join(ProjectStub.FOLDER + '~PROCESSED', 'data', 'TEST'),
                         service.volume_path())

    def test_get_working_directory_no_wd_set_and_src_set(self):
        service = module.Service({'roles': ['src']},
                                 dont_call_init_data=True)

        self.assertEqual(CONTAINER_SRC_PATH, service.get_working_directory())

    def test_get_working_directory_relative_wd_set_and_src_set(self):
        service = module.Service({'working_directory': 'relative_path/in/test', 'roles': ['src']},
                                 dont_call_init_data=True)

        self.assertEqual(CONTAINER_SRC_PATH + '/relative_path/in/test', service.get_working_directory())

    def test_get_working_directory_absolute_wd_set_and_src_set(self):
        service = module.Service({'working_directory': '/path/in/test', 'roles': ['?']},
                                 dont_call_init_data=True)

        self.assertEqual('/path/in/test', service.get_working_directory())

    def test_get_working_directory_no_wd_set_and_src_not_set(self):
        service = module.Service({'roles': ['?']},
                                 dont_call_init_data=True)

        self.assertEqual(None, service.get_working_directory())

    def test_get_working_directory_relative_wd_set_and_src_not_set(self):
        service = module.Service({'working_directory': 'relative_path/in/test', 'roles': ['?']},
                                 dont_call_init_data=True)

        self.assertEqual(None, service.get_working_directory())

    def test_get_working_directory_absolute_wd_set_and_src_not_set(self):
        service = module.Service({'working_directory': '/path/in/test', 'roles': ['?']},
                                 dont_call_init_data=True)

        self.assertEqual('/path/in/test', service.get_working_directory())

    def test_domain_not_main(self):
        system = YamlConfigDocumentStub({'proxy': {'url': 'TEST-URL'}})
        project = ProjectStub({'name': 'TEST-PROJECT'}, parent=system)
        app = YamlConfigDocumentStub({}, parent=project)
        service = module.Service({'$name': 'TEST-SERVICE', 'roles': ['?']},
                                 dont_call_init_data=True, parent=app)

        self.assertEqual('TEST-PROJECT__TEST-SERVICE.TEST-URL', service.domain())

    def test_domain_main(self):
        system = YamlConfigDocumentStub({'proxy': {'url': 'TEST-URL'}})
        project = ProjectStub({'name': 'TEST-PROJECT'}, parent=system)
        app = YamlConfigDocumentStub({}, parent=project)
        service = module.Service({'$name': 'TEST-SERVICE', 'roles': ['main']},
                                 dont_call_init_data=True, parent=app)

        self.assertEqual('TEST-PROJECT.TEST-URL', service.domain())

    @mock.patch("riptide.config.document.service.getuid", return_value=1234)
    def test_os_user(self, getuid_mock: Mock):
        service = module.Service({}, dont_call_init_data=True)
        self.assertEqual("1234", service.os_user())
        getuid_mock.assert_called_once()

    @mock.patch("riptide.config.document.service.getgid", return_value=1234)
    def test_os_group(self, getgid_mock: Mock):
        service = module.Service({}, dont_call_init_data=True)
        self.assertEqual("1234", service.os_group())
        getgid_mock.assert_called_once()

    def test_host_address(self):
        service = module.Service({}, dont_call_init_data=True)
        self.assertEqual(RIPTIDE_HOST_HOSTNAME, service.host_address())

    def test_home_path(self):
        service = module.Service({}, dont_call_init_data=True)
        self.assertEqual(CONTAINER_HOME_PATH, service.home_path())

    @mock.patch("os.path.dirname", return_value='CALLED DIRNAME')
    @mock.patch("riptide.config.document.service.open")
    @mock.patch("os.makedirs")
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("riptide.config.document.service.get_config_file_path", return_value='CALLED')
    def test_config_file_does_not_exist(self,
                                        get_config_file_path_mock: Mock, exists_mock: Mock,
                                        makedirs_mock: Mock, open_mock: Mock, dirname_mock: Mock):

        service = module.Service({}, dont_call_init_data=True)

        self.assertEqual('CALLED', service.config('FROM'))
        get_config_file_path_mock.assert_called_once_with('FROM', service)
        # os.path.exists?
        exists_mock.assert_called_once_with('CALLED')
        # NO:
        # os.path.dirname
        dirname_mock.assert_called_once_with('CALLED')
        # os.makedirs
        makedirs_mock.assert_called_once_with('CALLED DIRNAME', exist_ok=True)
        # open
        open_mock.assert_called_once_with('CALLED', 'a')
        # close
        open_mock.return_value.close.assert_called_once()


    @mock.patch("os.makedirs")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("riptide.config.document.service.get_config_file_path", return_value='CALLED')
    def test_config_file_does_exist(self,
                                        get_config_file_path_mock: Mock, exists_mock: Mock,
                                        makedirs_mock: Mock,):

        service = module.Service({}, dont_call_init_data=True)

        self.assertEqual('CALLED', service.config('FROM'))
        get_config_file_path_mock.assert_called_once_with('FROM', service)
        # os.path.exists?
        exists_mock.assert_called_once_with('CALLED')
        # YES
        makedirs_mock.assert_not_called()
