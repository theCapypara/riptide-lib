from configcrunch.tests.test_utils import YamlConfigDocumentStub


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
