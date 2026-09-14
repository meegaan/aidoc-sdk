"""
Public SDK API
==============

Stable public interface for AIDoc SDK.

Responsibilities:

- Handle extraction
- Compute source hash
- Run pipeline
- Return final AIDoc

This is the recommended integration surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from aidoc_sdk.pipeline.pipeline import Pipeline
from aidoc_sdk.pipeline.config import PipelineConfig
from aidoc_sdk.exceptions import AIDocTypeError


# ============================================================================
# FILE PROCESSING
# ============================================================================


def process_file(
    path: str | Path,
    format_name: Optional[str] = None,
    config: Optional[PipelineConfig] = None,
):
    """
    High-level document processing entrypoint.

    Args:
        path: file path
        format_name: (Optional) explicit registered extractor name
        config: optional pipeline configuration

    Returns:
        AIDoc
    """

    if not isinstance(path, (str, Path)):
        raise AIDocTypeError("path must be str or Path")

    pipeline = Pipeline(config=config)
    return pipeline.parse_file(path, format_name=format_name)


# ============================================================================
# BYTES PROCESSING
# ============================================================================


def process_bytes(
    data: bytes,
    format_name: str,
    config: Optional[PipelineConfig] = None,
):
    """
    Process in-memory bytes.
    """

    if not isinstance(data, bytes):
        raise AIDocTypeError("data must be bytes")

    pipeline = Pipeline(config=config)
    return pipeline.parse_bytes(data, format_name=format_name)
