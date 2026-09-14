from __future__ import annotations

"""
AIDoc Public SDK Surface
========================

Stable public API façade for the AIDoc SDK.

Design Principles:

- Deterministic canonical core
- Optional semantic enrichment via Pipeline
- Strict error taxonomy
- Controlled public surface
- No global logging configuration

Public Entry Points:

    process_file()
    process_bytes()
    Pipeline
    PipelineConfig
    ExecutionMode
    AIDoc
    structural_fingerprint()
    full_document_fingerprint()
"""

import logging

from aidoc_sdk.core import (
    AIDoc,
    structural_fingerprint,
    full_document_fingerprint,
)

from aidoc_sdk.interfaces import (
    process_file,
    process_bytes,
)

from aidoc_sdk.pipeline import (
    Pipeline,
    PipelineConfig,
    ExecutionMode,
)

from aidoc_sdk.semantic import (
    SemanticEngine,
    RuleEngine,
    LLMEngine,
)

from aidoc_sdk.exceptions import (
    AIDocError,
    AIDocTypeError,
    AIDocValueError,
    NormalizationError,
    ParsingError,
    SerializationError,
    IntegrityError,
    StructuralViolationError,
    DeterminismViolationError,
    ExtractionError,
    ExtractorConflictError,
    SemanticError,
    EngineExecutionError,
    StageExecutionError,
    AIDocIOError,
    DecodeError,
)

from aidoc_sdk.version import __version__


# ---------------------------------------------------------------------------
# Logging Policy
# ---------------------------------------------------------------------------

logging.getLogger(__name__).addHandler(logging.NullHandler())


# ---------------------------------------------------------------------------
# Public Surface
# ---------------------------------------------------------------------------

__all__ = [
    # High-level processing
    "process_file",
    "process_bytes",

    # Pipeline
    "Pipeline",
    "PipelineConfig",
    "ExecutionMode",

    # Models
    "AIDoc",

    # Fingerprints
    "structural_fingerprint",
    "full_document_fingerprint",

    # Semantic
    "SemanticEngine",
    "RuleEngine",
    "LLMEngine",

    # Errors
    "AIDocError",
    "AIDocTypeError",
    "AIDocValueError",
    "NormalizationError",
    "ParsingError",
    "SerializationError",
    "IntegrityError",
    "StructuralViolationError",
    "DeterminismViolationError",
    "ExtractionError",
    "ExtractorConflictError",
    "SemanticError",
    "EngineExecutionError",
    "StageExecutionError",
    "AIDocIOError",
    "DecodeError",

    # Version
    "__version__",
]
