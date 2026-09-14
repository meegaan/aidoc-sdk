"""
Pipeline Execution Interface
============================

High-level SDK pipeline interface.

Responsibilities:

- Accept RawDocument
- Initialize execution context
- Configure canonical + semantic stages
- Execute via orchestrator
- Return final AIDoc

This layer does NOT perform extraction.
Extraction should be done before invoking pipeline.
"""

from __future__ import annotations

from typing import Optional, List

from aidoc_sdk.pipeline.config import PipelineConfig
from aidoc_sdk.pipeline.context import PipelineContext
from aidoc_sdk.pipeline.stages import (
    PipelineStage,
    ExtractionStage,
    CanonicalStage,
    MetadataStage,
    SemanticStage,
)
from aidoc_sdk.pipeline.orchestrator import PipelineOrchestrator

from aidoc_sdk.core.models import AIDoc
from aidoc_sdk.exceptions import AIDocTypeError


class Pipeline:
    """
    High-level orchestration entrypoint.
    """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self._config = config or PipelineConfig()

        # Bootstrap built-in extractors and engines
        self._bootstrap_builtins()

    # ------------------------------------------------------------------
    # Built-in Extractor Bootstrap
    # ------------------------------------------------------------------

    def _bootstrap_builtins(self) -> None:
        """
        Load all built-in extractors and semantic engines.

        Safe to call multiple times — Python's import system ensures idempotency.
        """

        # Always available
        import aidoc_sdk.extraction.txt  # noqa: F401

        # Optional extractors
        try:
            import aidoc_sdk.extraction.docx  # noqa: F401
        except (ImportError, ModuleNotFoundError):
            pass

        try:
            import aidoc_sdk.extraction.pdf.extractor  # noqa: F401
        except (ImportError, ModuleNotFoundError):
            pass

        # Built-in engines
        import aidoc_sdk.semantic.rule_engine  # noqa: F401

    # ------------------------------------------------------------------
    # High-Level API
    # ------------------------------------------------------------------

    def parse_file(
        self,
        path: str | Path,
        format_name: Optional[str] = None,
    ) -> AIDoc:
        """
        Convenience method for file-based processing.
        """
        from pathlib import Path
        context = PipelineContext(
            config=self._config,
            input_path=Path(path),
            format_name=format_name,
        )
        return self.execute_context(context)

    def parse_bytes(
        self,
        data: bytes,
        format_name: str,
    ) -> AIDoc:
        """
        Convenience method for bytes-based processing.
        """
        context = PipelineContext(
            config=self._config,
            input_bytes=data,
            format_name=format_name,
        )
        return self.execute_context(context)

    # ------------------------------------------------------------------
    # Sync Execution
    # ------------------------------------------------------------------

    def execute_context(self, context: PipelineContext) -> AIDoc:
        """
        Execute pipeline on a pre-configured context.
        """
        orchestrator = PipelineOrchestrator(self._build_stages())
        result_context = orchestrator.run(context)
        
        if result_context.canonical_document is None:
             raise AIDocTypeError("Pipeline failed to produce a canonical document")
             
        return result_context.canonical_document

    def run(
        self,
        raw_document,
        source_hash: str,
        extractor_name: str,
        extractor_version: str,
    ) -> AIDoc:
        """
        Legacy run method. Maintains backward compatibility.
        """
        context = PipelineContext(
            config=self._config,
            raw_document=raw_document,
            extractor_name=extractor_name,
            extractor_version=extractor_version,
            artifacts={"source_hash": source_hash},
        )
        return self.execute_context(context)

    # ------------------------------------------------------------------
    # Async Execution
    # ------------------------------------------------------------------

    async def execute_context_async(self, context: PipelineContext) -> AIDoc:
        """
        Async execution on a pre-configured context.
        """
        orchestrator = PipelineOrchestrator(self._build_stages())
        result_context = await orchestrator.run_async(context)
        
        if result_context.canonical_document is None:
             raise AIDocTypeError("Pipeline failed to produce a canonical document (async)")
             
        return result_context.canonical_document

    async def run_async(
        self,
        raw_document,
        source_hash: str,
        extractor_name: str,
        extractor_version: str,
    ) -> AIDoc:
        """
        Legacy async run method.
        """
        context = PipelineContext(
            config=self._config,
            raw_document=raw_document,
            extractor_name=extractor_name,
            extractor_version=extractor_version,
            artifacts={"source_hash": source_hash},
        )
        return await self.execute_context_async(context)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _build_stages(self) -> List[PipelineStage]:

        stages = [
            ExtractionStage(),
            CanonicalStage(),
            MetadataStage(),
        ]

        if self._config.enable_semantic:
            stages.append(
                SemanticStage(
                    engine_names=self._config.semantic_engines
                )
            )

        return stages
