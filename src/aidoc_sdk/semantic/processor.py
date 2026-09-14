"""
Semantic Enrichment Node
========================

Executes semantic engines under strict structural guardrails.

Design Guarantees:

- Engine input document is never mutated
- Structural fingerprint must remain unchanged
- Spec version must remain unchanged
- Source hash must remain unchanged
- Only block.semantic and processor.semantic_layers may change
- Processor metadata injection handled here (not by engine)

This module enforces enrichment safety.
"""

from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)

from aidoc_sdk.core.models import (
    AIDoc,
    ProcessorInfo,
    SemanticLayerInfo,
)
from aidoc_sdk.core.guardrails import (
    assert_structure_unchanged,
    assert_same_spec,
    assert_same_source_hash,
)
from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.exceptions import (
    AIDocTypeError,
    EngineExecutionError,
)


class SemanticProcessor:
    """
    Guarded semantic enrichment executor / orchestrator.
    """

    def __init__(self, engines: List[SemanticEngine], fail_fast: bool = True) -> None:
        if not isinstance(engines, list):
            raise AIDocTypeError("engines must be a list")

        self._engines = engines
        self._fail_fast = fail_fast

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def process(self, document: AIDoc) -> AIDoc:
        if not isinstance(document, AIDoc):
            raise AIDocTypeError("SemanticProcessor expects AIDoc")

        current_doc = document

        for engine in self._engines:
            status = "success"
            err_msg = None

            try:
                enriched_doc = engine.process(current_doc)
                
                # ----------------------------------------------------------
                # Guardrails Enforcement
                # ----------------------------------------------------------

                assert_same_spec(current_doc, enriched_doc)
                assert_same_source_hash(current_doc, enriched_doc)
                assert_structure_unchanged(current_doc, enriched_doc)

            except Exception as exc:
                if self._fail_fast:
                    raise EngineExecutionError(
                        f"Engine '{engine.name}' execution failed"
                    ) from exc

                logger.error(
                    "Semantic Engine '%s' failed: %s",
                    engine.name, exc, exc_info=True
                )

                status = "failed"
                err_msg = str(exc)
                enriched_doc = current_doc  # Revert to unaltered baseline

            # ----------------------------------------------------------
            # Metadata Injection (controlled)
            # ----------------------------------------------------------

            enriched_doc = self._inject_processor_metadata(
                enriched_doc,
                engine.name,
                engine.version,
                status=status,
                error=err_msg
            )

            current_doc = enriched_doc

        return current_doc

    async def process_async(self, document: AIDoc) -> AIDoc:
        if not isinstance(document, AIDoc):
            raise AIDocTypeError("SemanticProcessor expects AIDoc")

        current_doc = document

        for engine in self._engines:
            status = "success"
            err_msg = None

            try:
                enriched_doc = await engine.process_async(current_doc)
                
                # ----------------------------------------------------------
                # Guardrails Enforcement
                # ----------------------------------------------------------

                assert_same_spec(current_doc, enriched_doc)
                assert_same_source_hash(current_doc, enriched_doc)
                assert_structure_unchanged(current_doc, enriched_doc)

            except Exception as exc:
                if self._fail_fast:
                    raise EngineExecutionError(
                        f"Engine '{engine.name}' execution failed (async)"
                    ) from exc

                logger.error(
                    "Semantic Engine '%s' failed: %s",
                    engine.name, exc, exc_info=True
                )

                status = "failed"
                err_msg = str(exc)
                enriched_doc = current_doc  # Revert to unaltered baseline

            # ----------------------------------------------------------
            # Metadata Injection (controlled)
            # ----------------------------------------------------------

            enriched_doc = self._inject_processor_metadata(
                enriched_doc,
                engine.name,
                engine.version,
                status=status,
                error=err_msg
            )

            current_doc = enriched_doc

        return current_doc

      # ------------------------------------------------------------------
    # Metadata Injection
    # ------------------------------------------------------------------

    def _inject_processor_metadata(  # noqa: PLR6301 (method kept for symmetry)
        self,
        document: AIDoc,
        engine_name: str,
        engine_version: str,
        status: str = "success",
        error: str | None = None,
    ) -> AIDoc:
        """
        Append semantic layer info to processor metadata.

        Processor metadata must already exist.
        """

        meta = document.meta
        processor = meta.processor

        # ProcessorInfo MUST exist. Pipeline layer is responsible for initial injection.
        if processor is None:
             raise EngineExecutionError(
                f"Processor metadata missing in document for engine '{engine_name}'"
            )

        new_layer = SemanticLayerInfo(
            name=engine_name,
            version=engine_version,
            status=status,
            error=error,
        )

        updated_layers = list(processor.semantic_layers)
        updated_layers.append(new_layer)

        updated_processor = processor.model_copy(
            update={"semantic_layers": updated_layers}
        )

        # Rebuild document immutably
        return document.model_copy(
            update={
                "meta": meta.model_copy(update={"processor": updated_processor})
            }
        )
