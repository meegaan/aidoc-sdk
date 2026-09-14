from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Tuple, Type

from aidoc_sdk.core.raw import RawDocument


class BaseExtractor(ABC):
    """
    Base class for extraction adapters.

    Responsibilities:
    - Convert external formats into RawDocument
    - Must NOT perform normalization
    - Must NOT perform hashing
    - Must NOT perform canonicalization
    """

    name: str
    version: str
    supported_extensions: Tuple[str, ...]

    @abstractmethod
    def extract(self, path: Path) -> RawDocument:
        """
        Extract canonical document elements from the given file path.
        """
        ...

    def extract_from_bytes(self, data: bytes) -> RawDocument:
        """
        Legacy handler for in-memory bytes where path is not provided.
        By default, most extractors will still need to override this,
        or they write to a temporary file before calling `extract()`.
        """
        raise NotImplementedError("extract_from_bytes must be overridden for direct bytes parsing")

    def extract_from_stream(self, stream: BinaryIO) -> RawDocument:
        data = stream.read()
        return self.extract_from_bytes(data)

    def extract_from_path(self, path: Path) -> RawDocument:
        """Backwards-compatibility alias for extract()"""
        return self.extract(path)
