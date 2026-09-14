"""
AIDoc Core Package
==================

Deterministic canonical contract for AIDoc.

Exposes:

- AIDoc (canonical document model)
- RawDocument (extraction output model)
- normalize_text
- hash_text
- hash_bytes
- structural_fingerprint
- full_document_fingerprint

Internal modules remain private.
"""

from aidoc_sdk.core.models import AIDoc
from aidoc_sdk.core.raw import RawDocument
from aidoc_sdk.core.normalizer import normalize_text
from aidoc_sdk.core.hashing import hash_text, hash_bytes
from aidoc_sdk.core.fingerprints import (
    structural_fingerprint,
    full_document_fingerprint,
)

__all__ = [
    "AIDoc",
    "RawDocument",
    "normalize_text",
    "hash_text",
    "hash_bytes",
    "structural_fingerprint",
    "full_document_fingerprint",
]
