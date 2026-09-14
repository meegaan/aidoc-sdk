"""
Canonical Fingerprinting
========================

Defines structural and full-document fingerprinting rules.

Design Principles:

- Structural fingerprint MUST NOT include processor metadata
- Structural fingerprint MUST NOT include semantic enrichment
- Full fingerprint includes entire canonical document
- Fingerprints rely exclusively on canonical JSON bytes
- Deterministic and stable across environments

Changing structural fingerprint rules requires MAJOR SDK_VERSION bump.
"""

from __future__ import annotations

from typing import Dict, Any

from aidoc_sdk.core.models import AIDoc
from aidoc_sdk.core.serializer import to_canonical_bytes
from aidoc_sdk.core.hashing import hash_canonical_json
from aidoc_sdk.exceptions import AIDocTypeError


# ============================================================================
# INTERNAL STRUCTURAL VIEW
# ============================================================================


def _build_structural_view(doc: AIDoc) -> Dict[str, Any]:
    """
    Build a structure-only representation of AIDoc.

    Excludes:
        - meta.processor
        - block.semantic
        - meta.created_at

    Includes:
        - spec
        - source_hash
        - sections
        - block IDs
        - block text
        - table rows
    """

    if not isinstance(doc, AIDoc):
        raise AIDocTypeError("_build_structural_view expects AIDoc")

    sections = []

    for section in doc.sections:
        blocks = []

        for block in section.blocks:
            if block.type == "paragraph":
                blocks.append({
                    "id": block.id,
                    "type": "paragraph",
                    "text": block.text,
                })
            elif block.type == "table":
                blocks.append({
                    "id": block.id,
                    "type": "table",
                    "rows": block.rows,
                })

        sections.append({
            "id": section.id,
            "title": section.title,
            "level": section.level,
            "blocks": blocks,
        })

    return {
        "spec": doc.spec,
        "source_hash": doc.meta.source_hash,
        "sections": sections,
    }


# ============================================================================
# STRUCTURAL FINGERPRINT
# ============================================================================


def structural_fingerprint(doc: AIDoc) -> str:
    """
    Compute fingerprint of structural content only.

    Safe for validating enrichment did not alter structure.
    """

    structural_view = _build_structural_view(doc)

    # Serialize structural view deterministically
    from json import dumps

    json_bytes = dumps(
        structural_view,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return hash_canonical_json(json_bytes)


# ============================================================================
# FULL DOCUMENT FINGERPRINT
# ============================================================================


def full_document_fingerprint(doc: AIDoc) -> str:
    """
    Compute fingerprint of entire canonical document,
    including processor metadata and semantic enrichment.
    """

    json_bytes = to_canonical_bytes(doc)
    return hash_canonical_json(json_bytes)
