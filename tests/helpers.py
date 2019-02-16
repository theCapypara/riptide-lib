from unittest import mock

from configcrunch.test_utils import YamlConfigDocumentStub


class _WithYcdMock:
    def __init__(self, ycd):
        self.mock = mock.patch.object(ycd, '__init__', side_effect=_ycd_set_doc)

    def __enter__(self):
        self.mock.__enter__()

    def __exit__(self, type, value, traceback):
        self.mock.__exit__(type, value, traceback)


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
