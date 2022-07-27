from riptide.tests.configcrunch_test_utils import YamlConfigDocumentStub


class ProjectStub(YamlConfigDocumentStub):
    """
    Projects stub that has some of the methods that a regular project would have.
    """
    FOLDER = 'FOLDER'
    SRC_FOLDER = 'SRC_FOLDER'

    def folder(self):
        return self.__class__.FOLDER

    def src_folder(self):
        return self.__class__.SRC_FOLDER


def process_config_stub(volumes, config_name, config, service, bind_path, regenerate=True):
    # TODO: Unit test for riptide.config.service.config_files.process_config!
    service_name = service['__UNIT_TEST_NAME'] if '__UNIT_TEST_NAME' in service else ''
    volumes[f"{config_name}~{config['from']}~{service_name}~{regenerate}"] = {
        'bind': bind_path, 'mode': 'STUB'
    }
