"""
Deterministic Rule-Based Semantic Engine
========================================

Provides lightweight semantic enrichment using rule-based detection.

Design Guarantees:

- Fully deterministic
- No randomness
- No external dependencies
- No structure mutation
- Only enriches block.semantic
- Returns new AIDoc instance

Rules Implemented:

- Obligation detection (must, shall, required)
- Condition detection (if ... then ...)
- Definition detection (means, defined as)
- Reference detection (Section X, Clause Y)

This engine is safe for structural guardrails.
"""

from __future__ import annotations

import re
from typing import List

from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.semantic.registry import engine
from aidoc_sdk.core.models import (
    AIDoc,
    Section,
    ParagraphBlock,
    TableBlock,
    Statement,
    Definition,
    Requirement,
    Prohibition,
    Condition,
    Reference,
    LogicException,
    Instruction,
    SemanticType,
    ReferenceType,
)


# ============================================================================
# PRECOMPILED RULE PATTERNS
# ============================================================================

REQUIREMENT_PATTERN = re.compile(r"\b(must|shall|required)\b", re.IGNORECASE)
PROHIBITION_PATTERN = re.compile(r"\b(shall not|must not|prohibited)\b", re.IGNORECASE)
CONDITION_PATTERN = re.compile(r"\bif\b.*\bthen\b", re.IGNORECASE)
DEFINITION_PATTERN = re.compile(r"\b(means|defined as)\b", re.IGNORECASE)
REFERENCE_PATTERN = re.compile(r"\b(section|clause)\s+\d+", re.IGNORECASE)
EXCEPTION_PATTERN = re.compile(r"\b(unless|except for)\b", re.IGNORECASE)
INSTRUCTION_PATTERN = re.compile(r"\b(to\s+\w+,\s+\w+|click|open|select)\b", re.IGNORECASE)


@engine("rule_engine")
class RuleEngine(SemanticEngine):
    """
    Deterministic rule-based semantic engine.
    
    Uses regular expressions to identify common legal and technical
    patterns such as requirements, prohibitions, conditions, and definitions.
    """

    name = "rule_engine"
    version = "1.0"

    # ------------------------------------------------------------------
    # Main Entry
    # ------------------------------------------------------------------

    def process(self, document: AIDoc) -> AIDoc:
        """
        Produce a new AIDoc with rule-based semantic annotations.
        """
        new_sections: List[Section] = []

        for section in document.sections:
            new_blocks = []
            for block in section.blocks:
                if isinstance(block, ParagraphBlock):
                    enriched_block = self._enrich_paragraph(block)
                else:
                    enriched_block = block
                new_blocks.append(enriched_block)

            new_sections.append(
                Section(
                    id=section.id,
                    title=section.title,
                    level=section.level,
                    blocks=new_blocks,
                )
            )

        return AIDoc(
            spec=document.spec,
            meta=document.meta,
            sections=new_sections,
        )

    # ------------------------------------------------------------------
    # Paragraph Enrichment
    # ------------------------------------------------------------------

    def _enrich_paragraph(self, block: ParagraphBlock) -> ParagraphBlock:
        """Apply regex rules to text."""
        text = block.text
        semantics = list(block.semantic)

        # 1-3. Primary Category Detection (Mutually Exclusive for regex)
        # Priority: Prohibition > Requirement > Instruction
        if PROHIBITION_PATTERN.search(text):
            semantics.append(
                Prohibition(
                    type=SemanticType.prohibition,
                    subject="unspecified",
                    action=text,
                    modality="prohibited",
                )
            )
        elif REQUIREMENT_PATTERN.search(text):
            semantics.append(
                Requirement(
                    type=SemanticType.requirement,
                    subject="unspecified",
                    action=text,
                    modality="mandatory",
                )
            )
        elif INSTRUCTION_PATTERN.search(text):
            semantics.append(
                Instruction(
                    type=SemanticType.instruction,
                    action=text,
                    target="unspecified",
                )
            )

        # 4. Condition Detection (Can co-exist with others)
        if CONDITION_PATTERN.search(text):
            semantics.append(
                Condition(
                    type=SemanticType.condition,
                    trigger=text,
                    effect="unspecified",
                )
            )

        # 4. Definition Detection
        if DEFINITION_PATTERN.search(text):
            semantics.append(
                Definition(
                    type=SemanticType.definition,
                    term=text.split()[0],
                    meaning=text,
                )
            )

        # 5. Reference Detection
        if REFERENCE_PATTERN.search(text):
            semantics.append(
                Reference(
                    type=SemanticType.reference,
                    target=text,
                    ref_type=ReferenceType.internal,
                )
            )

        # 6. Exception Detection (Logic Gate)
        if EXCEPTION_PATTERN.search(text):
            semantics.append(
                LogicException(
                    type=SemanticType.exception,
                    provision=text,
                    exemption="unspecified",
                )
            )

        if not semantics:
            return block

        return ParagraphBlock(
            id=block.id,
            type="paragraph",
            text=block.text,
            semantic=semantics,
        )
