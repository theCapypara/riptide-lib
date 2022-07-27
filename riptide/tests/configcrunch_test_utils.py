from schema import Schema
from typing import List

from configcrunch import YamlConfigDocument


class YamlConfigDocumentStub(YamlConfigDocument):
    """
    Minimal version of an actual YamlConfigDocument for use in unit tests.
    Apart from the constructor setting the fields doc, path and parent, no other fields
    are available.
    Accessors are available for doc.
    All other methods that modify the state are not available.
    """
    def __init__(self,
                 document: dict,
                 path: str = None,
                 parent: 'YamlConfigDocument' = None,
                 already_loaded_docs: List[str] = None,
                 set_parent_to_self=False,
                 absolute_paths=None
    ):
        """The option set_parent_to_self can be used to set the parent_doc to self for easier testing."""
        self.doc = document
        self.path = path
        self.absolute_path = absolute_paths
        self.parent_doc = parent
        if set_parent_to_self:
            self.parent_doc = self


    @classmethod
    def from_yaml(cls, path_to_yaml: str) -> 'YamlConfigDocument':
        raise NotImplementedError("not available for stub")

    @classmethod
    def header(cls) -> str:
        raise NotImplementedError("not available for stub")

    @classmethod
    def schema(cls) -> Schema:
        raise NotImplementedError("not available for stub")

    def validate(self) -> bool:
        raise NotImplementedError("not available for stub")

    def _initialize_data_before_merge(self):
        raise NotImplementedError("not available for stub")

    def _initialize_data_after_merge(self):
        raise NotImplementedError("not available for stub")

    def _initialize_data_after_variables(self):
        raise NotImplementedError("not available for stub")

    def resolve_and_merge_references(self, lookup_paths: List[str]) -> 'YamlConfigDocument':
        raise NotImplementedError("not available for stub")

    def process_vars(self) -> 'YamlConfigDocument':
        raise NotImplementedError("not available for stub")

    def process_vars_for(self, target: str) -> str:
        raise NotImplementedError("not available for stub")

    def parent(self) -> 'YamlConfigDocument':
        return self.parent_doc

    # Magic methods for accessing doc are left from super.

    def __repr__(self) -> str:
        return super().__repr__()

    def __str__(self):
        return super().__str__()

    def __len__(self):
        return super().__len__()

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    def __delitem__(self, key):
        super().__delitem__(key)

    def __iter__(self):
        return super().__iter__()

    def items(self):
        raise NotImplementedError("not available for stub")

    def to_dict(self):
        raise NotImplementedError("not available for stub")