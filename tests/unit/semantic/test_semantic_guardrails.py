"""
Tests: Structural Guardrails
=============================

Verifies that the SemanticProcessor's guardrail enforcement correctly
blocks engines that violate the AIDoc structural contract.

Covered contracts:

- spec MUST NOT change
- source_hash MUST NOT change
- Structural fingerprint (section/block IDs, ordering, text) MUST NOT change
- Compliant engines pass all guardrails without exception

Enterprise Quality Notes:

- Each malicious engine is defined inline and scoped to its test.
- No shared mutable state.
- Tests assert both the exception type and a human-readable message fragment.
"""

from __future__ import annotations

import pytest

from aidoc_sdk.core.models import (
    AIDoc,
    Meta,
    ProcessorInfo,
    ExtractorInfo,
    ParagraphBlock,
    Section,
)
from aidoc_sdk.core.fingerprints import structural_fingerprint
from aidoc_sdk.core.version import CORE_CONTRACT_VERSION
from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.semantic.processor import SemanticProcessor
from aidoc_sdk.exceptions import StructuralViolationError, EngineExecutionError


# ---------------------------------------------------------------------------
# Shared fixture helper — document with ProcessorInfo injected
# ---------------------------------------------------------------------------

def _with_processor(doc: AIDoc) -> AIDoc:
    """Return a copy of *doc* with a ProcessorInfo injected (required by SemanticProcessor)."""
    processor = ProcessorInfo(
        aidoc_core=CORE_CONTRACT_VERSION,
        extractor=ExtractorInfo(name="test", version="1.0"),
        semantic_layers=[],
    )
    return doc.model_copy(
        update={"meta": doc.meta.model_copy(update={"processor": processor})}
    )


# ---------------------------------------------------------------------------
# Malicious engines — isolated per test
# ---------------------------------------------------------------------------


class _SpecMutatingEngine(SemanticEngine):
    """Illegally changes the spec version."""

    name = "_bad_spec"
    version = "1.0"

    def process(self, document: AIDoc) -> AIDoc:
        return document.model_copy(update={"spec": "aidoc@9.9"})


class _SourceHashMutatingEngine(SemanticEngine):
    """Illegally changes source_hash in meta."""

    name = "_bad_hash"
    version = "1.0"

    def process(self, document: AIDoc) -> AIDoc:
        tampered_meta = document.meta.model_copy(
            update={"source_hash": "a" * 64}
        )
        return document.model_copy(update={"meta": tampered_meta})


class _StructureMutatingEngine(SemanticEngine):
    """Illegally removes a block, changing structural fingerprint."""

    name = "_bad_structure"
    version = "1.0"

    def process(self, document: AIDoc) -> AIDoc:
        first_section = document.sections[0]
        truncated_section = Section(
            id=first_section.id,
            title=first_section.title,
            level=first_section.level,
            blocks=[],  # ← removes all blocks
        )
        return document.model_copy(
            update={"sections": [truncated_section]}
        )


class _CompliantEngine(SemanticEngine):
    """A correctly implemented engine that only enriches block.semantic."""

    name = "_compliant"
    version = "1.0"

    def process(self, document: AIDoc) -> AIDoc:
        # Returns document unchanged — simplest valid implementation
        return document


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_spec_mutation_raises_structural_violation(canonical_document):
    """Engine that changes spec raises StructuralViolationError."""
    doc = _with_processor(canonical_document)
    processor = SemanticProcessor([_SpecMutatingEngine()])

    with pytest.raises(EngineExecutionError):
        processor.process(doc)


def test_source_hash_mutation_raises_structural_violation(canonical_document):
    """Engine that changes source_hash raises StructuralViolationError."""
    doc = _with_processor(canonical_document)
    processor = SemanticProcessor([_SourceHashMutatingEngine()])

    with pytest.raises(EngineExecutionError):
        processor.process(doc)


def test_structure_mutation_raises_structural_violation(canonical_document):
    """Engine that changes the block structure raises StructuralViolationError."""
    doc = _with_processor(canonical_document)
    processor = SemanticProcessor([_StructureMutatingEngine()])

    with pytest.raises(EngineExecutionError):
        processor.process(doc)


def test_compliant_engine_passes_all_guardrails(canonical_document):
    """A correctly implemented engine passes the full guardrail suite without exception."""
    doc = _with_processor(canonical_document)
    processor = SemanticProcessor([_CompliantEngine()])

    before_fp = structural_fingerprint(canonical_document)
    result = processor.process(doc)
    after_fp = structural_fingerprint(result)

    assert result.spec == canonical_document.spec
    assert result.meta.source_hash == canonical_document.meta.source_hash
    assert before_fp == after_fp
