"""
Structural Guardrails
=====================

Provides integrity enforcement utilities for the deterministic core.

Design Principles:

- Structural fingerprint must remain stable across enrichment
- Any structural mutation must raise explicit error
- No silent mutation allowed
- No reliance on external state
- Deterministic and pure

This module is used by the semantic enrichment node.
"""

from __future__ import annotations

from aidoc_sdk.core.models import AIDoc
from aidoc_sdk.core.fingerprints import structural_fingerprint
from aidoc_sdk.exceptions import (
    AIDocTypeError,
    StructuralViolationError,
)


# ============================================================================
# STRUCTURAL INTEGRITY ENFORCEMENT
# ============================================================================


def assert_structure_unchanged(
    before: AIDoc,
    after: AIDoc,
) -> None:
    """
    Assert that structural fingerprint of two documents is identical.

    Used to validate that semantic enrichment did not modify:

    - Section ordering
    - Block ordering
    - Block IDs
    - Section IDs
    - Block text
    - Table rows
    - Source hash

    Raises:
        StructuralViolationError if structure differs.
    """

    if not isinstance(before, AIDoc):
        raise AIDocTypeError("assert_structure_unchanged expects AIDoc (before)")

    if not isinstance(after, AIDoc):
        raise AIDocTypeError("assert_structure_unchanged expects AIDoc (after)")

    before_fp = structural_fingerprint(before)
    after_fp = structural_fingerprint(after)

    if before_fp != after_fp:
        raise StructuralViolationError(
            "Structural integrity violation detected during enrichment"
        )


# ============================================================================
# OPTIONAL VALIDATION UTILITIES
# ============================================================================


def assert_same_spec(before: AIDoc, after: AIDoc) -> None:
    """
    Ensure spec version was not altered.
    """

    if before.spec != after.spec:
        raise StructuralViolationError(
            "Spec version cannot be modified during processing"
        )


def assert_same_source_hash(before: AIDoc, after: AIDoc) -> None:
    """
    Ensure source hash remains identical.
    """

    if before.meta.source_hash != after.meta.source_hash:
        raise StructuralViolationError(
            "Source hash cannot be modified during processing"
        )
