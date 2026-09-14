"""
AIDoc Extraction Package
========================

Pluggable extraction layer.

Exposes:

- BaseExtractor
- register_extractor
- get_extractor
- list_extractors

Concrete extractors (txt, pdf, docx) are not auto-imported
to avoid optional dependency side effects.
"""

from aidoc_sdk.extraction.base import BaseExtractor
from aidoc_sdk.extraction.registry import (
    register_extractor,
    get_extractor,
    list_extractors,
)

__all__ = [
    "BaseExtractor",
    "register_extractor",
    "get_extractor",
    "list_extractors",
]
