"""
Canonical Builder
=================

Transforms RawDocument into canonical immutable AIDoc.

Design Guarantees:

- Fully deterministic
- Stateless and pure
- No semantic enrichment
- No processor metadata injection
- No timestamp injection
- Block IDs derived from normalized content only
- Section IDs derived from level + normalized title
- Ordering strictly preserved

This module defines structural identity.
Changing behavior here requires MAJOR SDK_VERSION bump.
"""

from __future__ import annotations

from typing import List

from aidoc_sdk.core.raw import (
    RawDocument,
    RawParagraph,
    RawHeading,
    RawTable,
)
from aidoc_sdk.core.models import (
    AIDoc,
    Section,
    ParagraphBlock,
    TableBlock,
    Meta,
)
from aidoc_sdk.core.normalizer import normalize_text
from aidoc_sdk.core.hashing import hash_text
from aidoc_sdk.core.version import SPEC_VERSION
from aidoc_sdk.exceptions import AIDocTypeError


# ============================================================================
# INTERNAL ID BUILDERS
# ============================================================================


def _build_block_id(normalized_content: str) -> str:
    """
    Block ID = SHA-256 of normalized content only.
    """
    return hash_text(normalized_content)


def _build_section_id(level: int, normalized_title: str) -> str:
    """
    Section ID = SHA-256(level + ":" + normalized_title)
    """
    return hash_text(f"{level}:{normalized_title}")


# ============================================================================
# CANONICALIZATION ENTRYPOINT
# ============================================================================


def canonicalize(raw: RawDocument, source_hash: str) -> AIDoc:
    """
    Convert RawDocument to canonical AIDoc.

    Args:
        raw: extracted raw structure
        source_hash: SHA-256 of original source bytes

    Returns:
        Immutable AIDoc
    """

    if not isinstance(raw, RawDocument):
        raise AIDocTypeError("canonicalize expects RawDocument")

    if not isinstance(source_hash, str):
        raise AIDocTypeError("source_hash must be str")

    sections: List[Section] = []

    current_title = "Document"
    current_level = 1
    current_blocks = []

    for element in raw.elements:

        # ---------------------------------------------------------------
        # HEADINGS → Start new section
        # ---------------------------------------------------------------
        if isinstance(element, RawHeading):

            # Flush existing section if blocks exist
            if current_blocks:
                sections.append(
                    Section(
                        id=_build_section_id(current_level, current_title),
                        title=current_title,
                        level=current_level,
                        blocks=current_blocks,
                    )
                )
                current_blocks = []

            normalized_title = normalize_text(element.text)
            current_title = normalized_title
            current_level = element.level

        # ---------------------------------------------------------------
        # PARAGRAPH
        # ---------------------------------------------------------------
        elif isinstance(element, RawParagraph):

            normalized_text = normalize_text(element.text)

            block = ParagraphBlock(
                id=_build_block_id(normalized_text),
                type="paragraph",
                text=normalized_text,
            )

            current_blocks.append(block)

        # ---------------------------------------------------------------
        # TABLE
        # ---------------------------------------------------------------
        elif isinstance(element, RawTable):

            normalized_rows = [
                [normalize_text(cell) for cell in row]
                for row in element.rows
            ]

            flat_representation = "\n".join(
                ["\t".join(row) for row in normalized_rows]
            )

            block = TableBlock(
                id=_build_block_id(flat_representation),
                type="table",
                rows=normalized_rows,
            )

            current_blocks.append(block)

    # ---------------------------------------------------------------
    # Flush Final Section
    # ---------------------------------------------------------------
    if current_blocks:
        sections.append(
            Section(
                id=_build_section_id(current_level, current_title),
                title=current_title,
                level=current_level,
                blocks=current_blocks,
            )
        )

    return AIDoc(
        spec=SPEC_VERSION,
        meta=Meta(
            source_hash=source_hash,
        ),
        sections=sections,
    )
