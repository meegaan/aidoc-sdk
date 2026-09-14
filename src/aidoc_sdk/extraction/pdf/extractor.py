from __future__ import annotations

from typing import Any, List

from aidoc_sdk.extraction.base import BaseExtractor
from aidoc_sdk.extraction.registry import extractor
from aidoc_sdk.core.raw import (
    RawDocument,
    RawParagraph,
    RawTable,
)
from aidoc_sdk.exceptions import AIDocTypeError, AIDocValueError

from .tables import extract_tables_from_page


# ---------------------------------------------------------------------------
# PDF Extractor (v1)
# ---------------------------------------------------------------------------
# - Optional dependency (pdfplumber)
# - Extracts text paragraphs
# - Extracts tables via table helper
# - No normalization
# - No hashing
# ---------------------------------------------------------------------------


@extractor("pdf")
class PDFExtractor(BaseExtractor):
    name = "pdf"
    version = "1.0"
    supported_extensions = (".pdf",)

    def __init__(self):
        super().__init__()
        try:
            import pdfplumber
        except ImportError as e:
            raise AIDocValueError(
                "PDF extraction requires 'pdfplumber'. "
                "Install via: pip install aidoc-sdk[pdf]"
            ) from e

    def extract(self, path: Path) -> RawDocument:
        import pdfplumber

        elements: List = []
        order = 0

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:

                # Extract tables first
                tables = extract_tables_from_page(page)
                for table in tables:
                    elements.append(
                        RawTable(
                            order=order,
                            rows=table,
                        )
                    )
                    order += 1

                # Extract text
                text = page.extract_text() or ""
                for line in text.split("\n"):
                    line = line.strip()
                    if line:
                        elements.append(
                            RawParagraph(
                                order=order,
                                text=line,
                            )
                        )
                        order += 1

        return RawDocument(elements=elements)


# Extractor registered via decorator
