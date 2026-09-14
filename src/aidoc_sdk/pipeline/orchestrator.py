"""
Pipeline Orchestrator
=====================

Executes ordered pipeline stages.

Design Principles:

- Stage order strictly preserved
- Sync and async execution supported
- No stage mutation
- No cross-stage coupling
- Clear error isolation
"""

from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)

from aidoc_sdk.pipeline.context import PipelineContext
from aidoc_sdk.pipeline.stages import PipelineStage
from aidoc_sdk.pipeline.config import ExecutionMode
from aidoc_sdk.exceptions import StageExecutionError


class PipelineOrchestrator:
    """
    Executes configured pipeline stages.
    """

    def __init__(self, stages: List[PipelineStage]) -> None:
        self._stages = stages

    # ------------------------------------------------------------------
    # Sync Execution
    # ------------------------------------------------------------------

    def run(self, context: PipelineContext) -> PipelineContext:

        current_context = context

        for stage in self._stages:
            logger.debug("Running stage: %s", stage.name)
            try:
                current_context = stage.execute(current_context)
            except Exception as exc:
                raise StageExecutionError(
                    f"Stage '{stage.name}' failed"
                ) from exc

        return current_context

    # ------------------------------------------------------------------
    # Async Execution
    # ------------------------------------------------------------------

    async def run_async(self, context: PipelineContext) -> PipelineContext:

        current_context = context

        for stage in self._stages:
            logger.debug("Running stage (async): %s", stage.name)
            try:
                current_context = await stage.execute_async(current_context)
            except Exception as exc:
                raise StageExecutionError(
                    f"Stage '{stage.name}' failed (async)"
                ) from exc

        return current_context
