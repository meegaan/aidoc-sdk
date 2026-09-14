"""
Extraction Bootstrap Loader
============================

Loads built-in extractors so they register themselves.

This module centralizes built-in registration.
It avoids side effects in package __init__.
"""

from __future__ import annotations

def load_builtins() -> None:
    """Import built-in extraction modules to trigger their @extractor decorators."""
    # Built-in extractors (always available)
    from aidoc_sdk.extraction.txt import TxtExtractor  # noqa: F401

    # Optional extractors (guarded)
    try:
        from aidoc_sdk.extraction.docx import DocxExtractor  # noqa: F401
    except Exception:
        pass

    try:
        from aidoc_sdk.extraction.pdf.extractor import PdfExtractor  # noqa: F401
    except Exception:
        pass
