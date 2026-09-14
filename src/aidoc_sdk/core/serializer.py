"""
Canonical JSON Serialization
============================

Provides deterministic JSON serialization for all canonical AIDoc models.

Design Guarantees:

- UTF-8 strict encoding
- Stable key ordering (sort_keys=True)
- No indentation
- No pretty formatting
- Compact separators (",", ":")
- Recursive null removal
- No dynamic exclusions
- No environment-dependent behavior

This module is part of the deterministic core contract.

Changing:
- separators
- encoding
- key sorting
- null stripping behavior
- dump mode

REQUIRES MAJOR SDK_VERSION bump.
"""

from __future__ import annotations

import json
from typing import Any, Final

from pydantic import BaseModel

from aidoc_sdk.exceptions import AIDocTypeError, SerializationError


# ============================================================================
# CONSTANTS (IMMUTABLE)
# ============================================================================

ENCODING: Final[str] = "utf-8"
JSON_SEPARATORS: Final[tuple[str, str]] = (",", ":")


# ============================================================================
# INTERNAL NULL STRIPPING (RECURSIVE)
# ============================================================================


def _remove_nulls(obj: Any) -> Any:
    """
    Recursively remove None values from dictionaries.

    Lists preserve order.
    Dictionary key order is preserved prior to final sorting in json.dumps.
    """

    if isinstance(obj, dict):
        return {
            key: _remove_nulls(value)
            for key, value in obj.items()
            if value is not None
        }

    if isinstance(obj, list):
        return [_remove_nulls(item) for item in obj]

    return obj


# ============================================================================
# CANONICAL DICT CONVERSION
# ============================================================================


def to_canonical_dict(model: BaseModel) -> dict:
    """
    Convert Pydantic model into canonical dictionary representation.

    Guarantees:
    - Includes all defined fields
    - Does not exclude unset fields
    - Removes nulls deterministically
    """

    if not isinstance(model, BaseModel):
        raise AIDocTypeError("to_canonical_dict expects BaseModel")

    try:
        raw = model.model_dump(
            mode="json",
            by_alias=False,
            exclude_none=False,
        )
    except Exception as exc:
        raise SerializationError("Model dump failed") from exc

    return _remove_nulls(raw)


# ============================================================================
# CANONICAL JSON STRING
# ============================================================================


def to_canonical_json(model: BaseModel) -> str:
    """
    Deterministic JSON serialization of canonical model.
    """

    canonical_dict = to_canonical_dict(model)

    try:
        return json.dumps(
            canonical_dict,
            sort_keys=True,
            ensure_ascii=False,
            separators=JSON_SEPARATORS,
        )
    except Exception as exc:
        raise SerializationError("JSON serialization failed") from exc


# ============================================================================
# CANONICAL BYTE REPRESENTATION (FOR HASHING)
# ============================================================================


def to_canonical_bytes(model: BaseModel) -> bytes:
    """
    Deterministic UTF-8 byte encoding of canonical JSON.
    """

    json_str = to_canonical_json(model)

    try:
        return json_str.encode(ENCODING, errors="strict")
    except Exception as exc:
        raise SerializationError("UTF-8 encoding failed") from exc
