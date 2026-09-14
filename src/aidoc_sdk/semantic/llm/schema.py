"""
LLM Semantic Output Schema
==========================

Defines strict validation models for LLM-produced semantic annotations.

Design Principles:

- LLM output is untrusted
- Must validate structure before converting to SemanticObject
- No direct injection into canonical models
- Schema must be deterministic and strict
- No dynamic fields allowed

This schema does NOT modify AIDoc directly.
Conversion into canonical semantic objects happens in engine layer.
"""

from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# BASE LLM SEMANTIC ITEM
# ============================================================================


class LLMBaseSemantic(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    type: str


# ============================================================================
# DESCRIPTIVE
# ============================================================================


class LLMStatement(LLMBaseSemantic):
    type: Literal["statement"]
    content: str
    confidence: float = Field(ge=0.0, le=1.0)


class LLMDefinition(LLMBaseSemantic):
    type: Literal["definition"]
    term: str
    meaning: str
    confidence: float = Field(ge=0.0, le=1.0)


class LLMReference(LLMBaseSemantic):
    type: Literal["reference"]
    target: str
    ref_type: Literal["internal", "external"]
    confidence: float = Field(ge=0.0, le=1.0)


# ============================================================================
# NORMATIVE
# ============================================================================


class LLMRequirement(LLMBaseSemantic):
    type: Literal["requirement"]
    subject: str
    action: str
    object: Optional[str] = None
    modality: str
    confidence: float = Field(ge=0.0, le=1.0)


class LLMProhibition(LLMBaseSemantic):
    type: Literal["prohibition"]
    subject: str
    action: str
    object: Optional[str] = None
    modality: str
    confidence: float = Field(ge=0.0, le=1.0)


# ============================================================================
# PROCEDURAL
# ============================================================================


class LLMInstruction(LLMBaseSemantic):
    type: Literal["instruction"]
    action: str
    target: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


# ============================================================================
# CONDITIONAL
# ============================================================================


class LLMCondition(LLMBaseSemantic):
    type: Literal["condition"]
    trigger: str
    effect: str
    confidence: float = Field(ge=0.0, le=1.0)


class LLMLogicException(LLMBaseSemantic):
    type: Literal["exception"]
    provision: str
    exemption: str
    confidence: float = Field(ge=0.0, le=1.0)


# ============================================================================
# UNION
# ============================================================================


LLMSemanticItem = (
    LLMStatement
    | LLMDefinition
    | LLMReference
    | LLMRequirement
    | LLMProhibition
    | LLMInstruction
    | LLMCondition
    | LLMLogicException
)


class LLMResponse(BaseModel):
    """
    Validated response from LLM before conversion.
    """

    model_config = ConfigDict(extra="forbid")

    items: List[LLMSemanticItem]
