from __future__ import annotations

from configcrunch import YamlConfigDocument
from riptide.config.document import DocumentClass, RiptideDocument
from schema import Schema


class YamlConfigDocumentStub(RiptideDocument):
    _doc_class: DocumentClass

    @property
    def identity(self) -> DocumentClass:
        return self._doc_class

    @identity.setter
    def identity(self, value: DocumentClass):
        self._doc_class = value

    @classmethod
    def make(
        cls,
        doc_class: DocumentClass,
        document: dict,
        path: str | None = None,
        parent: RiptideDocument | None = None,
        set_parent_to_self=False,
        absolute_paths=None,
    ):
        slf = cls.from_dict(document)
        slf.path = path
        slf.parent_doc = parent
        slf._doc_class = doc_class
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
    def subdocuments(cls) -> list[tuple[str, type[YamlConfigDocument]]]:
        raise NotImplementedError("not available for stub")
