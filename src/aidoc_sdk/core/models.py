"""
AIDoc Canonical Data Model
==========================

Defines the immutable, deterministic canonical document schema.

Core Guarantees:

- Fully immutable (frozen models)
- No unknown fields (extra="forbid")
- Strict SHA-256 ID enforcement
- Discriminated unions for structural safety
- No runtime mutation allowed
- No dynamic defaults
- Semantic enrichment MUST NOT alter structure
- Processor metadata MUST NOT affect structural fingerprint

Changing any structural element in this file requires:
    MAJOR SDK_VERSION bump
    SPEC_VERSION bump

This module is part of the deterministic core contract.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Literal, Annotated
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator

from aidoc_sdk.exceptions import AIDocValueError
from aidoc_sdk.core.version import SPEC_VERSION


# ============================================================================
# INTERNAL SHA-256 VALIDATION
# ============================================================================


def _validate_sha256_hex(value: str) -> str:
    if len(value) != 64:
        raise AIDocValueError("Invalid SHA-256 hash length")
    try:
        int(value, 16)
    except ValueError:
        raise AIDocValueError("Hash must be valid hex-encoded SHA-256")
    return value


# ============================================================================
# SEMANTIC ENUMERATIONS
# ============================================================================


class SemanticType(str, Enum):
    # --- Descriptive (The "What") ---
    # Static context that doesn't change behavior.
    statement = "statement"     # General info (e.g., "The sun is hot.")
    definition = "definition"   # Glossary/Terms (e.g., "A 'Patient' is...")
    reference = "reference"     # Pointers (e.g., "See Appendix A.")

    # --- Normative (The "Must/Must Not") ---
    # Rules that govern behavior or state.
    requirement = "requirement" # Positive obligation (Do this).
    prohibition = "prohibition" # Negative obligation (Don't do this).

    # --- Procedural (The "How") ---
    # Sequences of actions.
    instruction = "instruction" # Steps to follow (1. Open, 2. Click).

    # --- Conditional (The "If/Unless") ---
    # The logic gates that turn other types on or off.
    condition = "condition"     # Prerequisites (IF this happens...).
    exception = "exception"     # Overrides/Exemptions (UNLESS this happens...)


class ReferenceType(str, Enum):
    internal = "internal"
    external = "external"


# ============================================================================
# SEMANTIC OBJECTS (DISCRIMINATED UNION)
# ============================================================================


class SemanticBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    type: SemanticType


class Statement(SemanticBase):
    """General informational text or assertion."""
    type: Literal[SemanticType.statement]
    content: str


class Definition(SemanticBase):
    """Defines a concept or term."""
    type: Literal[SemanticType.definition]
    term: str
    meaning: str


class Reference(SemanticBase):
    """Pointer to another section, source, or document."""
    type: Literal[SemanticType.reference]
    target: str
    ref_type: ReferenceType


class Requirement(SemanticBase):
    """Rule, obligation, or mandate (Positive)."""
    type: Literal[SemanticType.requirement]
    subject: str
    action: str
    object: Optional[str] = None
    modality: str
    deadline: Optional[str] = None


class Prohibition(SemanticBase):
    """Negative obligation (Don't do this)."""
    type: Literal[SemanticType.prohibition]
    subject: str
    action: str
    object: Optional[str] = None
    modality: str


class Instruction(SemanticBase):
    """Action or procedural step."""
    type: Literal[SemanticType.instruction]
    action: str
    target: Optional[str] = None


class Condition(SemanticBase):
    """Prerequisite or dependency (Logic Gate)."""
    type: Literal[SemanticType.condition]
    trigger: str
    effect: str


class LogicException(SemanticBase):
    """Overrides or exemptions (Logic Gate)."""
    type: Literal[SemanticType.exception]
    provision: str
    exemption: str


SemanticObject = Annotated[
    Statement
    | Definition
    | Reference
    | Requirement
    | Prohibition
    | Instruction
    | Condition
    | LogicException,
    Field(discriminator="type"),
]


# ============================================================================
# STRUCTURAL BLOCKS
# ============================================================================


class BlockBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    id: str
    semantic: List[SemanticObject] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        return _validate_sha256_hex(v)


class ParagraphBlock(BlockBase):
    type: Literal["paragraph"]
    text: str


class TableBlock(BlockBase):
    type: Literal["table"]
    rows: List[List[str]]

    @field_validator("rows")
    @classmethod
    def validate_rectangular(cls, v: List[List[str]]) -> List[List[str]]:
        if not v:
            raise AIDocValueError("Table cannot be empty")

        width = len(v[0])
        for row in v:
            if len(row) != width:
                raise AIDocValueError("Table must be rectangular")

        return v


Block = Annotated[
    ParagraphBlock | TableBlock,
    Field(discriminator="type"),
]


# ============================================================================
# SECTION
# ============================================================================


class Section(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    id: str
    title: str
    level: int = Field(ge=1)
    blocks: List[Block]

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        return _validate_sha256_hex(v)


# ============================================================================
# PROCESSOR METADATA
# ============================================================================


class ExtractorInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    version: str


class SemanticLayerInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    version: str
    status: Literal["success", "failed"] = "success"
    error: Optional[str] = None


class ProcessorInfo(BaseModel):
    """
    Processor metadata is operational metadata.

    MUST NOT:
    - Influence structural fingerprint
    - Modify canonical sections
    - Alter block identity

    Semantic enrichment is allowed to append to semantic_layers only.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    aidoc_core: str
    extractor: ExtractorInfo
    semantic_layers: List[SemanticLayerInfo] = Field(default_factory=list)


class Meta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_hash: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    processor: Optional[ProcessorInfo] = None

    @field_validator("source_hash")
    @classmethod
    def validate_source_hash(cls, v: str) -> str:
        return _validate_sha256_hex(v)

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise AIDocValueError("created_at must be ISO-8601 formatted")
        return v
        
    @field_validator("updated_at")
    @classmethod
    def validate_updated_at(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise AIDocValueError("updated_at must be ISO-8601 formatted")
        return v

# ============================================================================
# ROOT DOCUMENT
# ============================================================================


class AIDoc(BaseModel):
    """
    Canonical immutable document.

    Guarantees:
    - spec must match SPEC_VERSION exactly
    - sections order preserved
    - structural integrity enforced via fingerprint layer
    - enrichment must preserve structure
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    spec: Literal[SPEC_VERSION]
    meta: Meta
    sections: List[Section]
