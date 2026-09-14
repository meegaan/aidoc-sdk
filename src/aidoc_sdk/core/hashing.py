"""
Deterministic Hashing Utilities
===============================

Defines canonical hashing primitives used throughout AIDoc.

Design Guarantees:

- Algorithm: SHA-256
- Encoding: UTF-8 (strict)
- Stateless and pure
- No dynamic salt
- No randomness
- No environment dependency
- Lowercase hex output only
- Stable across Python versions

Changing any of the following requires MAJOR SDK_VERSION bump:

- Hashing algorithm
- Encoding rules
- Digest format
- Byte preparation rules

This module is part of the deterministic core contract.
"""

from __future__ import annotations

import hashlib
from typing import Final

from aidoc_sdk.exceptions import AIDocTypeError, IntegrityError


# ============================================================================
# CONSTANTS (IMMUTABLE)
# ============================================================================

ENCODING: Final[str] = "utf-8"
HASH_HEX_LENGTH: Final[int] = 64


# ============================================================================
# INTERNAL SHA-256 IMPLEMENTATION
# ============================================================================


def _sha256_hex(data: bytes) -> str:
    """
    Compute SHA-256 digest of raw bytes.

    Returns:
        64-character lowercase hexadecimal string.
    """

    if not isinstance(data, bytes):
        raise AIDocTypeError("_sha256_hex expects bytes")

    digest = hashlib.sha256(data).hexdigest()

    if len(digest) != HASH_HEX_LENGTH:
        raise IntegrityError("Invalid SHA-256 digest length")

    # hashlib always returns lowercase hex, but enforce explicitly
    if not digest.isalnum():
        raise IntegrityError("Invalid SHA-256 hex output")

    return digest


# ============================================================================
# PUBLIC HASHING FUNCTIONS
# ============================================================================


def hash_text(text: str) -> str:
    """
    Deterministically hash UTF-8 encoded text.

    Strict encoding:
        - Raises on invalid characters
        - No implicit fallback
    """

    if not isinstance(text, str):
        raise AIDocTypeError("hash_text expects str")

    encoded = text.encode(ENCODING, errors="strict")
    return _sha256_hex(encoded)


def hash_bytes(raw: bytes) -> str:
    """
    Deterministically hash raw bytes.
    """

    if not isinstance(raw, bytes):
        raise AIDocTypeError("hash_bytes expects bytes")

    return _sha256_hex(raw)


def hash_canonical_json(json_bytes: bytes) -> str:
    """
    Hash canonical JSON byte representation.

    Input MUST:
        - Already be serialized canonically
        - Use UTF-8 strict encoding
        - Have stable key ordering
    """

    if not isinstance(json_bytes, bytes):
        raise AIDocTypeError("hash_canonical_json expects bytes")

    return _sha256_hex(json_bytes)
