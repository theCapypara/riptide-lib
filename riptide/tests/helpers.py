import os

from unittest import mock

from unittest.mock import Mock

from configcrunch.tests.test_utils import YamlConfigDocumentStub
from riptide.db.driver.abstract import AbstractDbDriver


class _WithYcdMock:
    def __init__(self, ycd):
        self.mock = mock.patch.object(ycd, '__init__', side_effect=_ycd_set_doc)

    def __enter__(self):
        self.mock.__enter__()

    def __exit__(self, type, value, traceback):
        self.mock.__exit__(type, value, traceback)


class _DbDriverMock:
    def __init__(self, db_driver_get_path):
        self.mocked_driver = Mock(AbstractDbDriver)
        self.mocked_get = mock.patch(db_driver_get_path, return_value=self.mocked_driver)

    def __enter__(self):
        return self.mocked_get.__enter__(), self.mocked_driver

    def __exit__(self, type, value, traceback):
        self.mocked_get.__exit__(type, value, traceback)


def _ycd_set_doc(self, document, **kwargs):
    self.doc = document


def patch_ycd_mock(ycd):
    """
    Patches the provided YamlConfigDocument with a Mock class of that type.
    Instances of this patched class have the following fields stubbed:
    - doc: Returns the value of the document parameter passed with the constructor
    """
    return _WithYcdMock(ycd)


def side_effect_for_load_subdocument():
    """
    Returns a side effect function creating a stub instance of YCDD.
    Used for testing calls to load_subdocument.
    """
    def func(value, *args, **kwargs):
        return YamlConfigDocumentStub(value)
    return func


def patch_mock_db_driver(db_driver_get_path):
    """
    Patches a mock object for db_driver_for_service and returns a mock db driver
    that is returned by it, as well as the patched db_driver_for_service:
    :return: (db_driver_for_service_mock, db_driver_mock)
    """
    return _DbDriverMock(db_driver_get_path)


def get_fixture_paths():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            'fixtures'
        )
    )


def get_fixture_path(name):
    """
    Load a yaml fixture file, name relative to fixtures dir.
    """
    return os.path.join(get_fixture_paths(), name)
