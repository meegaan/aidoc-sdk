"""
AIDoc Pipeline Package
======================

Public orchestration surface for document processing.

Exposes:
- Pipeline
- PipelineConfig
- ExecutionMode

Internal modules (stages, context, orchestrator) are intentionally hidden.
"""

from aidoc_sdk.pipeline.pipeline import Pipeline
from aidoc_sdk.pipeline.config import PipelineConfig, ExecutionMode

__all__ = [
    "Pipeline",
    "PipelineConfig",
    "ExecutionMode",
]
