"""
AIDoc Exception Hierarchy (STABLE PUBLIC CONTRACT)
--------------------------------------------------

Design Principles:

- All SDK errors inherit from AIDocError
- No raw Python exceptions leak past boundaries
- Clear separation of failure domains
- Stage-aware and engine-aware error isolation
- Determinism violations explicitly represented

Adding new exceptions is MINOR change.
Removing or renaming is MAJOR change.
"""

from __future__ import annotations


# ===========================================================================
# BASE ERROR
# ===========================================================================


class AIDocError(Exception):
    """
    Root exception for all AIDoc SDK errors.
    """
    pass


# ===========================================================================
# INPUT / VALIDATION
# ===========================================================================


class AIDocTypeError(AIDocError, TypeError):
    """
    Raised when invalid type is provided to public API.
    """
    pass


class AIDocValueError(AIDocError, ValueError):
    """
    Raised when value violates deterministic or structural contract.
    """
    pass


class ConfigurationError(AIDocError):
    """
    Raised when pipeline or engine configuration is invalid.
    """
    pass


# ===========================================================================
# CORE PROCESSING ERRORS
# ===========================================================================


class NormalizationError(AIDocError):
    """
    Raised when normalization pipeline fails.
    """
    pass


class ParsingError(AIDocError):
    """
    Raised when canonicalization or structural parsing fails.
    """
    pass


class SerializationError(AIDocError):
    """
    Raised when canonical serialization fails.
    """
    pass


class IntegrityError(AIDocError):
    """
    Raised when hashing or fingerprint validation fails.
    """
    pass


class DeterminismViolationError(AIDocError):
    """
    Raised when a deterministic contract is violated.
    """
    pass


class StructuralViolationError(AIDocError):
    """
    Raised when enrichment modifies canonical structure.
    """
    pass


# ===========================================================================
# EXTRACTION LAYER
# ===========================================================================


class ExtractionError(AIDocError):
    """
    Raised when extraction adapter fails.
    """
    pass


class ExtractorConflictError(ExtractionError):
    """
    Raised when two extractors attempt to register the same file extension.
    """
    pass


# ===========================================================================
# SEMANTIC LAYER
# ===========================================================================


class SemanticError(AIDocError):
    """
    Base error for semantic processing.
    """
    pass


class EngineExecutionError(SemanticError):
    """
    Raised when semantic engine execution fails.
    """
    pass


# ===========================================================================
# PIPELINE LAYER
# ===========================================================================


class StageExecutionError(AIDocError):
    """
    Raised when a pipeline stage fails.
    """
    pass


# ===========================================================================
# IO / INTERFACE
# ===========================================================================


class AIDocIOError(AIDocError):
    """
    Raised when document loading or file IO fails.
    """
    pass


class DecodeError(AIDocError):
    """
    Raised when input bytes are not valid UTF-8.
    """
    pass


# ===========================================================================
# PUBLIC EXPORTS
# ===========================================================================

__all__ = [
    "AIDocError",
    "AIDocTypeError",
    "AIDocValueError",
    "ConfigurationError",
    "NormalizationError",
    "ParsingError",
    "SerializationError",
    "IntegrityError",
    "DeterminismViolationError",
    "StructuralViolationError",
    "ExtractionError",
    "ExtractorConflictError",
    "SemanticError",
    "EngineExecutionError",
    "StageExecutionError",
    "AIDocIOError",
    "DecodeError",
]
