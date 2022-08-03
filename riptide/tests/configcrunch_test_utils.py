from schema import Schema
from typing import List

from configcrunch import YamlConfigDocument


class YamlConfigDocumentStub(YamlConfigDocument):
    @classmethod
    def make(cls,
             document: dict,
             path: str = None,
             parent: 'YamlConfigDocument' = None,
             set_parent_to_self=False,
             absolute_paths=None
     ):
        slf = cls.from_dict(document)
        slf.path = path
        slf.parent_doc = parent
        if absolute_paths is not None:
            slf.absolute_paths = absolute_paths
        if set_parent_to_self:
            slf.parent_doc = slf
        return slf

    @classmethod
    def header(cls) -> str:
        raise NotImplementedError("not available for stub")

    @classmethod
    def schema(cls) -> Schema:
        raise NotImplementedError("not available for stub")

    @classmethod
    def subdocuments(cls) -> Schema:
        raise NotImplementedError("not available for stub")
