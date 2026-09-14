"""
Plain Text Extractor (v1)
-------------------------

Responsibilities:

- Convert UTF-8 text into RawDocument
- Preserve line order
- No normalization
- No hashing
- No semantic enrichment
- Deterministic behavior

Input Modes:

- extract_from_bytes (preferred)
- extract_from_path

Does NOT accept arbitrary objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from aidoc_sdk.extraction.base import BaseExtractor
from aidoc_sdk.extraction.registry import extractor
from aidoc_sdk.core.raw import RawDocument, RawParagraph
from aidoc_sdk.exceptions import AIDocTypeError, DecodeError


@extractor("txt")
class TxtExtractor(BaseExtractor):

    name = "txt"
    version = "1.0"
    supported_extensions = (".txt", ".md", ".csv", ".log", ".json", ".xml")

    # ------------------------------------------------------------------
    # Path Extraction
    # ------------------------------------------------------------------

    def extract(self, path: Path) -> RawDocument:
        try:
            data = path.read_bytes()
        except Exception as exc:
            raise DecodeError("Failed to read TXT file") from exc

        return self.extract_from_bytes(data)

    # ------------------------------------------------------------------
    # Bytes Extraction
    # ------------------------------------------------------------------

    def extract_from_bytes(self, data: bytes) -> RawDocument:
        if not isinstance(data, bytes):
            raise AIDocTypeError("TXT extractor expects bytes")

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DecodeError("Invalid UTF-8 input") from exc

        elements: List[RawParagraph] = []
        order = 0

        for line in text.splitlines():
            # Preserve original spacing — canonical layer handles normalization
            elements.append(
                RawParagraph(
                    order=order,
                    text=line,
                )
            )
            order += 1

        return RawDocument(elements=elements)
