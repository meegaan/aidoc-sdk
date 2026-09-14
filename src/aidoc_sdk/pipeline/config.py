"""
Pipeline Configuration
======================

Defines strongly-typed configuration for pipeline execution.

Design Principles:

- Fully typed
- Immutable
- No dynamic dict-based config
- Explicit execution mode
- Explicit engine selection
"""

from __future__ import annotations

from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ExecutionMode(str, Enum):
    sync = "sync"
    async_mode = "async"


class PipelineConfig(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    execution_mode: ExecutionMode = ExecutionMode.sync
    semantic_engines: Optional[List[str]] = None
    enable_semantic: bool = False
    semantic_fail_fast: bool = True
