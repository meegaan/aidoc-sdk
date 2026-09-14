"""
Deterministic Text Normalization
================================

Defines the canonical normalization pipeline used prior to hashing.

Design Guarantees:

- Fully deterministic
- Stateless and pure
- No environment-dependent behavior
- No locale dependence
- No dynamic configuration
- Safe for structural fingerprinting

Pipeline Order (STRICT — DO NOT REORDER):

1. Unicode normalization (NFKC)
2. Character replacement (ordered and immutable)
3. Line ending normalization → '\n'
4. Collapse spaces/tabs
5. Remove trailing spaces before newline
6. Collapse excessive blank lines (max two)
7. Final strip()

Changing any rule here requires:
    MAJOR SDK_VERSION bump
    CORE_CONTRACT_VERSION bump

This module is part of the deterministic core contract.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final

from aidoc_sdk.exceptions import AIDocTypeError


# ============================================================================
# PRECOMPILED REGEX (ASCII SAFE, DETERMINISTIC)
# ============================================================================

MULTISPACE_RE: Final = re.compile(r"[ \t]+", flags=re.ASCII)
TRAILING_SPACE_RE: Final = re.compile(r"[ \t]+\n", flags=re.ASCII)
EXCESS_NEWLINES_RE: Final = re.compile(r"\n{3,}")


# ============================================================================
# ORDERED CHARACTER REPLACEMENTS (IMMUTABLE)
# ============================================================================

CHAR_REPLACEMENTS: Final[tuple[tuple[str, str], ...]] = (
    ("“", '"'),
    ("”", '"'),
    ("‘", "'"),
    ("’", "'"),
    ("\u00A0", " "),  # Non-breaking space
)


# ============================================================================
# NORMALIZATION STEPS (INTERNAL)
# ============================================================================


def normalize_unicode(text: str) -> str:
    """
    Step 1: Unicode NFKC normalization.
    """
    if not isinstance(text, str):
        raise AIDocTypeError("normalize_unicode expects str")
    return unicodedata.normalize("NFKC", text)


def normalize_characters(text: str) -> str:
    """
    Step 2: Deterministic character replacement.
    Replacement order MUST remain unchanged.
    """
    if not isinstance(text, str):
        raise AIDocTypeError("normalize_characters expects str")

    for bad, good in CHAR_REPLACEMENTS:
        text = text.replace(bad, good)

    return text


def normalize_whitespace(text: str) -> str:
    """
    Steps 3–7: Whitespace normalization.
    """
    if not isinstance(text, str):
        raise AIDocTypeError("normalize_whitespace expects str")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse spaces and tabs
    text = MULTISPACE_RE.sub(" ", text)

    # Remove trailing spaces before newline
    text = TRAILING_SPACE_RE.sub("\n", text)

    # Collapse excessive blank lines (max two)
    text = EXCESS_NEWLINES_RE.sub("\n\n", text)

    # Final trim
    return text.strip()


# ============================================================================
# PUBLIC ENTRY POINT
# ============================================================================


def normalize_text(text: str) -> str:
    """
    Canonical deterministic normalization entrypoint.

    Raises:
        AIDocTypeError if input is not str.
    """

    if not isinstance(text, str):
        raise AIDocTypeError("normalize_text expects str")

    text = normalize_unicode(text)
    text = normalize_characters(text)
    text = normalize_whitespace(text)

    return text
