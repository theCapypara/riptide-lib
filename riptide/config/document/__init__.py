"""
The classes that process all configuration documents are placed in this package.

Each class represents one type of document.
"""

from abc import ABC
from enum import Enum, auto
from typing import ClassVar

from configcrunch import YamlConfigDocument


class DocumentClass(Enum):
    """
    Identification of a document. Each document type has an ``identity`` class attribute
    that maps to this enum corresponding to its type.

    This should be used instead of isinstance; for unit test mocking.
    """

    Config = auto()
    Project = auto()
    App = auto()
    Hook = auto()
    Service = auto()
    Command = auto()


class RiptideDocument(YamlConfigDocument, ABC):
    identity: ClassVar[DocumentClass]
