"""
Raw Extraction Models
=====================

Defines non-canonical structural output of extraction adapters.

Design Principles:

- Represents layout-extracted structure BEFORE canonicalization
- Not part of deterministic contract
- No hashing
- No semantic enrichment
- No processor metadata
- Fully immutable
- Minimal structural validation only

This module is NOT part of structural fingerprint contract.
"""

from __future__ import annotations

from typing import List, Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator

from aidoc_sdk.exceptions import AIDocValueError


# ============================================================================
# BASE RAW ELEMENT
# ============================================================================


class RawElement(BaseModel):
    """
    Base class for extracted elements.

    order:
        Absolute document order index.
        Must be non-negative.
        Must be unique per RawDocument.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    order: int = Field(ge=0)


# ============================================================================
# RAW STRUCTURAL TYPES
# ============================================================================


class RawParagraph(RawElement):
    text: str


class RawHeading(RawElement):
    text: str
    level: int = Field(ge=1)


class RawTable(RawElement):
    rows: List[List[str]]

    @field_validator("rows")
    @classmethod
    def validate_rows(cls, v: List[List[str]]) -> List[List[str]]:
        if not v:
            raise AIDocValueError("RawTable rows cannot be empty")
        return v


RawNode = Annotated[
    RawParagraph | RawHeading | RawTable,
    Field(discriminator=None),
]


# ============================================================================
# RAW DOCUMENT
# ============================================================================


class RawDocument(BaseModel):
    """
    Container for extracted elements.

    Guarantees:
    - Element order must be unique
    - Elements preserved exactly as extracted
    - No canonical processing
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    elements: List[RawNode]

    @field_validator("elements")
    @classmethod
    def validate_unique_order(cls, v: List[RawNode]) -> List[RawNode]:
        seen = set()
        for element in v:
            if element.order in seen:
                raise AIDocValueError(
                    "Duplicate element order detected in RawDocument"
                )
            seen.add(element.order)
        return v
