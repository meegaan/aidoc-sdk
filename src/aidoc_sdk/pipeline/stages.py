"""
Pipeline Stages
===============

Defines formal execution stages for pipeline orchestration.

Design Principles:

- Each stage receives PipelineContext
- Each stage returns NEW PipelineContext
- No stage mutates context in-place
- No stage mutates canonical models
- Sync + async support
- Clear failure boundary

Stages included:

- CanonicalStage
- SemanticStage
"""

from __future__ import annotations

import asyncio

from abc import ABC, abstractmethod
from typing import List, Optional, Any
from datetime import datetime, timezone
from aidoc_sdk.pipeline.context import PipelineContext
from aidoc_sdk.core.canonical import canonicalize
from aidoc_sdk.core.models import (
    AIDoc,
    ProcessorInfo,
    ExtractorInfo,
)
from aidoc_sdk.core.version import CORE_CONTRACT_VERSION
from aidoc_sdk.core.hashing import hash_bytes
from aidoc_sdk.extraction.registry import registry, get_extractor
from aidoc_sdk.semantic.processor import SemanticProcessor
from aidoc_sdk.semantic.registry import get_engine
from aidoc_sdk.exceptions import StageExecutionError, AIDocTypeError


# ============================================================================
# BASE STAGE CONTRACT
# ============================================================================


class PipelineStage(ABC):
    """
    Abstract stage contract.

    Stages implement `execute()` (sync), `execute_async()` (async), or both.

    - Sync-only stages: override `execute()` only.
    - Async-only stages: override `execute_async()` only.
      (the default `execute()` raises NotImplementedError with a clear message)
    - Dual-mode stages: override both.
    """

    name: str

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Synchronous execution.

        Override this for sync or dual-mode stages.
        Raises NotImplementedError for async-only stages.
        """
        raise NotImplementedError(
            f"Stage '{self.__class__.__name__}' is async-only. "
            "Use the async pipeline or override execute()."
        )

    async def execute_async(self, context: PipelineContext) -> PipelineContext:
        """
        Asynchronous execution. Defaults to the synchronous execute().
        Override this for async or dual-mode stages.
        """
        return self.execute(context)


# ============================================================================
# EXTRACTION STAGE
# ============================================================================


class ExtractionStage(PipelineStage):
    """
    Responsible for converting raw input (path or bytes) into a RawDocument.
    """

    name = "extraction"

    def execute(self, context: PipelineContext) -> PipelineContext:
        input_path = context.input_path
        input_bytes = context.input_bytes
        format_name = context.format_name

        if input_path:
            # File-based extraction
            if format_name:
                extractor = get_extractor(format_name)
            else:
                extractor = registry.for_file(input_path)

            source_bytes = input_path.read_bytes()
            raw_doc = extractor.extract(input_path)
            source_hash = hash_bytes(source_bytes)

        elif input_bytes:
            # Bytes-based extraction
            if not format_name:
                raise StageExecutionError("format_name required for bytes-based extraction")

            extractor = get_extractor(format_name)
            raw_doc = extractor.extract_from_bytes(input_bytes)
            source_hash = hash_bytes(input_bytes)

        else:
            # Fallback for manual Pipeline.run where raw_document is passed directly
            if context.raw_document:
                return context
            raise StageExecutionError("No input (path or bytes) provided for extraction")

        # Update artifacts with source_hash for CanonicalStage
        artifacts = context.artifacts.copy()
        artifacts["source_hash"] = source_hash

        return context.replace(
            raw_document=raw_doc,
            extractor_name=extractor.name,
            extractor_version=extractor.version,
            artifacts=artifacts,
        )


# ============================================================================
# CANONICALIZATION STAGE
# ============================================================================


class CanonicalStage(PipelineStage):

    name = "canonical"

    def execute(self, context: PipelineContext) -> PipelineContext:

        if context.raw_document is None:
            raise StageExecutionError("RawDocument missing in context")

        canonical_doc = canonicalize(
            raw=context.raw_document,
            source_hash=context.artifacts.get("source_hash"),
        )

        return context.replace(canonical_document=canonical_doc)


# ============================================================================
# METADATA INJECTION STAGE
# ============================================================================


class MetadataStage(PipelineStage):
    """
    Initializes ProcessorInfo in the canonical document.
    Must run after CanonicalStage and before SemanticStage.
    """

    name = "metadata"

    def __init__(
        self, 
        extractor_name: Optional[str] = None, 
        extractor_version: Optional[str] = None
    ) -> None:
        self._extractor_name = extractor_name
        self._extractor_version = extractor_version

    def execute(self, context: PipelineContext) -> PipelineContext:
        doc = context.canonical_document
        if doc is None:
            raise StageExecutionError("Canonical document missing for metadata injection")

        # Pull from context if not explicitly provided in constructor
        extractor_name = self._extractor_name or context.extractor_name
        extractor_version = self._extractor_version or context.extractor_version

        if not extractor_name or not extractor_version:
             raise StageExecutionError("Extractor metadata missing (name/version)")
        
        timestamp = datetime.now(timezone.utc).isoformat()
        processor = ProcessorInfo(
            aidoc_core=CORE_CONTRACT_VERSION,
            extractor=ExtractorInfo(
                name=extractor_name,
                version=extractor_version,
            ),
            semantic_layers=[],
        )
        new_meta = doc.meta.model_copy(
        update={
            "processor": processor,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
        print(timestamp)
        print(new_meta)
        new_doc = AIDoc(
            spec=doc.spec,
            meta=doc.meta.model_copy(update={"processor": processor}),
            sections=doc.sections,
        )

        return context.replace(canonical_document=new_doc)


# ============================================================================
# SEMANTIC ENRICHMENT STAGE
# ============================================================================


class SemanticStage(PipelineStage):

    name = "semantic"

    def __init__(self, engine_names: Optional[List[str]]) -> None:
        self._engine_names = engine_names or []

    def execute(self, context: PipelineContext) -> PipelineContext:

        if not context.config.enable_semantic:
            return context

        if context.canonical_document is None:
            raise StageExecutionError("Canonical document missing")

        engines = [get_engine(name) for name in self._engine_names]

        if not engines:
            return context

        processor = SemanticProcessor(
            engines,
            fail_fast=context.config.semantic_fail_fast
        )

        enriched_doc = processor.process(context.canonical_document)

        return context.replace(canonical_document=enriched_doc)

    async def execute_async(self, context: PipelineContext) -> PipelineContext:

        if not context.config.enable_semantic:
            return context

        if context.canonical_document is None:
            raise StageExecutionError("Canonical document missing")

        engines = [get_engine(name) for name in self._engine_names]

        if not engines:
            return context

        processor = SemanticProcessor(
            engines,
            fail_fast=context.config.semantic_fail_fast
        )

        # Support async engines using structural guardrails
        enriched_doc = await processor.process_async(context.canonical_document)

        return context.replace(canonical_document=enriched_doc)

