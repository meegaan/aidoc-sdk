"""
LLM Semantic Enrichment Engine
==============================

Provides async LLM-powered semantic enrichment.

Design Principles:

- Async-first
- Non-deterministic enrichment allowed
- Structural mutation forbidden
- Must validate LLM output via schema
- Must rebuild canonical blocks immutably
- Processor metadata injected by EnrichmentNode only

This engine enriches content but does NOT affect structure.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from aidoc_sdk.semantic.registry import engine
from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.semantic.llm.client import BaseLLMClient
from aidoc_sdk.semantic.llm.prompts import build_prompt
from aidoc_sdk.semantic.llm.decorators import retry_on_failure, log_execution, handle_provider_errors
from aidoc_sdk.semantic.llm.schema import (
    LLMResponse,
    LLMStatement,
    LLMDefinition,
    LLMReference,
    LLMRequirement,
    LLMProhibition,
    LLMInstruction,
    LLMCondition,
    LLMLogicException,
)
from aidoc_sdk.core.models import (
    AIDoc,
    Section,
    ParagraphBlock,
    Statement,
    Definition,
    Reference,
    Requirement,
    Prohibition,
    Instruction,
    Condition,
    LogicException,
    SemanticType,
    ReferenceType,
)
from aidoc_sdk.exceptions import SemanticError

logger = logging.getLogger(__name__)


@engine("llm_engine")
class LLMEngine(SemanticEngine):
    """
    LLM-powered semantic enrichment engine.
    
    Extracts semantic meaning from structural blocks using a provided 
    LLM client. Integrates seamlessly into the deterministic pipeline
    while safely handling the non-deterministic output of LLMs.
    """

    name = "llm_engine"
    version = "1.0"

    def __init__(
        self, 
        client: BaseLLMClient,
        custom_system_prompt: Optional[str] = None
    ) -> None:
        """
        Initialize the LLM Engine.
        
        Args:
            client: The LLM Provider client implementation.
            custom_system_prompt: Optional override for the LLM instructions.
        """
        self._client = client
        self._custom_system_prompt = custom_system_prompt

    # ------------------------------------------------------------------
    # Public Async Enrichment
    # ------------------------------------------------------------------

    async def process_async(self, document: AIDoc) -> AIDoc:
        logger.info("Starting LLMEngine processing on document: %s", document.meta.source_hash)
        new_sections: List[Section] = []

        for section in document.sections:
            new_blocks = []
            for block in section.blocks:
                if isinstance(block, ParagraphBlock):
                    enriched_block = await self._enrich_paragraph(block)
                else:
                    # Tables and other blocks are not enriched by default in v1
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
    # Sync Adapter
    # ------------------------------------------------------------------

    def process(self, document: AIDoc) -> AIDoc:
        """
        Synchronous fallback execution, raising an error to enforce
        safety since LLMs inherently require async network I/O.
        """
        raise SemanticError(
            "LLMEngine requires async execution to prevent blocking on network I/O. "
            "Please use process_async() or execute within an AsyncPipeline."
        )

    # ------------------------------------------------------------------
    # Paragraph Enrichment
    # ------------------------------------------------------------------

    @handle_provider_errors
    @retry_on_failure(retries=3, delay=1.0)
    @log_execution
    async def _enrich_paragraph(self, block: ParagraphBlock) -> ParagraphBlock:
        """
        Enrich a single paragraph by calling the LLM and parsing the response.
        """
        # 1. Build the instructional prompt
        prompt = build_prompt(block.text, self._custom_system_prompt)

        # 2. Call the LLM Provider
        raw_response = await self._client.generate(prompt)

        # 3. Validate structured output
        try:
            validated = LLMResponse.model_validate(raw_response)
        except Exception as e:
            logger.error("LLM returned structurally invalid JSON: %s", str(e))
            raise SemanticError(f"LLM Schema validation failed: {str(e)}") from e

        # 4. Map back to canonical SemanticObjects
        semantics = list(block.semantic)

        for item in validated.items:
            if isinstance(item, LLMStatement):
                semantics.append(
                    Statement(
                        type=SemanticType.statement,
                        content=item.content,
                    )
                )

            elif isinstance(item, LLMDefinition):
                semantics.append(
                    Definition(
                        type=SemanticType.definition,
                        term=item.term,
                        meaning=item.meaning,
                    )
                )

            elif isinstance(item, LLMReference):
                try:
                    ref_enum = ReferenceType(item.ref_type)
                except ValueError:
                    logger.warning("Invalid reference type '%s' returned by LLM, defaulting to 'internal'", item.ref_type)
                    ref_enum = ReferenceType.internal
                    
                semantics.append(
                    Reference(
                        type=SemanticType.reference,
                        target=item.target,
                        ref_type=ref_enum,
                    )
                )

            elif isinstance(item, LLMRequirement):
                semantics.append(
                    Requirement(
                        type=SemanticType.requirement,
                        subject=item.subject,
                        action=item.action,
                        object=item.object,
                        modality=item.modality,
                    )
                )

            elif isinstance(item, LLMProhibition):
                semantics.append(
                    Prohibition(
                        type=SemanticType.prohibition,
                        subject=item.subject,
                        action=item.action,
                        object=item.object,
                        modality=item.modality,
                    )
                )

            elif isinstance(item, LLMInstruction):
                semantics.append(
                    Instruction(
                        type=SemanticType.instruction,
                        action=item.action,
                        target=item.target,
                    )
                )

            elif isinstance(item, LLMCondition):
                semantics.append(
                    Condition(
                        type=SemanticType.condition,
                        trigger=item.trigger,
                        effect=item.effect,
                    )
                )

            elif isinstance(item, LLMLogicException):
                semantics.append(
                    LogicException(
                        type=SemanticType.exception,
                        provision=item.provision,
                        exemption=item.exemption,
                    )
                )

        if not semantics:
            return block

        # 5. Immutably rebuild block
        return ParagraphBlock(
            id=block.id,
            type="paragraph",
            text=block.text,
            semantic=semantics,
        )
