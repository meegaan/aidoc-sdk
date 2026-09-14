"""
Tests: Pipeline Engine Execution Order
=======================================

Verifies that the pipeline executes semantic engines in the exact order
declared in PipelineConfig.semantic_engines, and that the resulting
processor.semantic_layers accurately reflects this sequence.

Enterprise Quality Notes:

- Uses unique engine names prefixed with "_order_" to avoid registry pollution.
- Engines are cleaned up from the registry in teardown via pytest fixtures.
- Tests verify both layer names and their ordering.
"""

from __future__ import annotations

import pytest

from aidoc_sdk.core.models import AIDoc
from aidoc_sdk.core.version import CORE_CONTRACT_VERSION
from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.semantic.decorators import engine
from aidoc_sdk.semantic.registry import _ENGINE_REGISTRY
from aidoc_sdk.pipeline.config import PipelineConfig, ExecutionMode
from aidoc_sdk.pipeline.stages import SemanticStage, MetadataStage, CanonicalStage
from aidoc_sdk.pipeline.context import PipelineContext


# ---------------------------------------------------------------------------
# Registry cleanup fixture
# ---------------------------------------------------------------------------

ORDER_ENGINE_NAMES = ["_order_alpha", "_order_beta", "_order_gamma"]


@pytest.fixture(autouse=True)
def _cleanup_order_engines():
    """Remove order-test engines from the global registry after each test."""
    yield
    for name_ in ORDER_ENGINE_NAMES:
        _ENGINE_REGISTRY.pop(name_, None)


# ---------------------------------------------------------------------------
# Minimal engine factory
# ---------------------------------------------------------------------------

def _make_passthrough_engine(name_: str) -> type[SemanticEngine]:
    """Return a pass-through SemanticEngine that does not enrich."""

    class _E(SemanticEngine):
        name = name_
        version = "1.0"

        def process(self, document: AIDoc) -> AIDoc:
            return document

    _E.__name__ = f"_E_{name_}"
    return _E


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_engines_run_in_configured_order(canonical_document):
    """
    Pipeline must execute engines in the order declared in semantic_engines,
    and processor.semantic_layers must reflect that exact sequence.
    """
    alpha_name = "_order_alpha"
    beta_name = "_order_beta"

    alpha_cls = _make_passthrough_engine(alpha_name)
    beta_cls = _make_passthrough_engine(beta_name)

    # Manual registration (simulates external package import)
    from aidoc_sdk.semantic.registry import register_engine
    register_engine(alpha_cls)
    register_engine(beta_cls)

    config = PipelineConfig(
        enable_semantic=True,
        semantic_engines=[alpha_name, beta_name],
    )

    meta_stage = MetadataStage(extractor_name="test", extractor_version="1.0")
    sem_stage = SemanticStage(engine_names=[alpha_name, beta_name])

    context = PipelineContext(
        config=config,
        canonical_document=canonical_document,
    )
    context = meta_stage.execute(context)
    context = sem_stage.execute(context)

    result = context.canonical_document
    assert result is not None

    layers = result.meta.processor.semantic_layers
    layer_names = [layer.name for layer in layers]

    assert layer_names == [alpha_name, beta_name], (
        f"Expected engine order [{alpha_name!r}, {beta_name!r}], got {layer_names!r}"
    )


def test_multiple_engines_append_layers_sequentially(canonical_document):
    """
    With three engines configured, semantic_layers must contain
    exactly three entries in the correct sequence.
    """
    alpha_name = "_order_alpha"
    beta_name = "_order_beta"
    gamma_name = "_order_gamma"

    from aidoc_sdk.semantic.registry import register_engine
    for name_ in [alpha_name, beta_name, gamma_name]:
        register_engine(_make_passthrough_engine(name_))

    config = PipelineConfig(
        enable_semantic=True,
        semantic_engines=[alpha_name, beta_name, gamma_name],
    )

    meta_stage = MetadataStage(extractor_name="test", extractor_version="1.0")
    sem_stage = SemanticStage(engine_names=[alpha_name, beta_name, gamma_name])

    context = PipelineContext(
        config=config,
        canonical_document=canonical_document,
    )
    context = meta_stage.execute(context)
    context = sem_stage.execute(context)

    result = context.canonical_document
    assert result is not None

    layers = result.meta.processor.semantic_layers
    assert len(layers) == 3

    layer_names = [layer.name for layer in layers]
    assert layer_names == [alpha_name, beta_name, gamma_name], (
        f"Expected [{alpha_name!r}, {beta_name!r}, {gamma_name!r}], got {layer_names!r}"
    )
