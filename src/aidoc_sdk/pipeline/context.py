"""
Pipeline Execution Context
==========================

Container for data flowing through pipeline stages.

Design Principles:

- Immutable-by-replacement (stages return new context)
- No global state
- No hidden mutation
- Raw extraction isolated from canonical document
- Artifact storage for debugging/metrics

Context is orchestration-only.
Core models remain untouched.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from aidoc_sdk.core.raw import RawDocument
from aidoc_sdk.core.models import AIDoc
from aidoc_sdk.pipeline.config import PipelineConfig


class PipelineContext(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    config: PipelineConfig

    # Raw Input (provided at pipeline entry)
    input_path: Optional[Path] = None
    input_bytes: Optional[bytes] = None
    format_name: Optional[str] = None

    # Extraction Metadata (populated by ExtractionStage)
    extractor_name: Optional[str] = None
    extractor_version: Optional[str] = None

    # Raw extraction output
    raw_document: Optional[RawDocument] = None

    # Canonical document
    canonical_document: Optional[AIDoc] = None

    # Arbitrary artifacts (timings, logs, metrics, debug data, source_hash)
    artifacts: Dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------
    # Context Replacement Utility
    # ------------------------------------------------------------------

    def replace(self, **updates: Any) -> "PipelineContext":
        """
        Return new context with updated fields.
        """
        return self.model_copy(update=updates)
