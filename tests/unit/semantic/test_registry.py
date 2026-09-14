"""
Tests: Semantic Engine Registry
================================

Verifies the registration contract, decorator behaviour, and all
registry guardrails at the unit level.

Enterprise Quality Notes:

- Each test is isolated and self-contained.
- Fixtures use unique engine names to avoid cross-test registry pollution.
- No shared mutable state between tests.
"""

from __future__ import annotations

import pytest

from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.semantic.registry import (
    register_engine,
    get_engine,
    list_engines,
    _ENGINE_REGISTRY,
)
from aidoc_sdk.semantic.decorators import engine
from aidoc_sdk.core.models import AIDoc
from aidoc_sdk.exceptions import ConfigurationError


# ---------------------------------------------------------------------------
# Helpers — isolated engine definitions
# ---------------------------------------------------------------------------

def _make_minimal_engine(name_: str, version_: str = "1.0") -> type[SemanticEngine]:
    """Factory: return a fresh SemanticEngine subclass for each test."""

    class _Engine(SemanticEngine):
        name = name_
        version = version_

        def process(self, document: AIDoc) -> AIDoc:
            return document

    _Engine.__name__ = f"_Engine_{name_}"
    return _Engine


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_engine_success():
    """register_engine stores a valid engine and get_engine returns an instance."""
    name_ = "_test_reg_success"
    cls = _make_minimal_engine(name_)

    try:
        register_engine(cls)
        instance = get_engine(name_)
        assert isinstance(instance, cls)
    finally:
        _ENGINE_REGISTRY.pop(name_, None)


def test_register_engine_duplicate_raises():
    """Registering the same engine name twice raises ConfigurationError."""
    name_ = "_test_reg_dup"
    cls = _make_minimal_engine(name_)

    try:
        register_engine(cls)
        with pytest.raises(ConfigurationError, match="already registered"):
            register_engine(cls)
    finally:
        _ENGINE_REGISTRY.pop(name_, None)


def test_register_engine_non_subclass_raises():
    """Registering a class that is not a SemanticEngine subclass raises ConfigurationError."""

    class NotAnEngine:
        name = "_test_not_subclass"
        version = "1.0"

    with pytest.raises(ConfigurationError, match="must subclass SemanticEngine"):
        register_engine(NotAnEngine)  # type: ignore[arg-type]


def test_get_engine_unknown_raises():
    """get_engine for an unregistered name raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="No semantic engine registered"):
        get_engine("__definitely_not_registered__")


def test_list_engines_includes_registered_name():
    """list_engines returns a list that includes the registered engine name."""
    name_ = "_test_list_engines"
    cls = _make_minimal_engine(name_)

    try:
        register_engine(cls)
        assert name_ in list_engines()
    finally:
        _ENGINE_REGISTRY.pop(name_, None)


# ---------------------------------------------------------------------------
# @engine decorator
# ---------------------------------------------------------------------------


def test_engine_decorator_registers_on_import():
    """@engine("name") automatically registers the engine class."""
    name_ = "_test_decorator_reg"

    try:
        @engine(name_)
        class _DecoratedEngine(SemanticEngine):
            name = name_
            version = "1.0"

            def process(self, document: AIDoc) -> AIDoc:
                return document

        instance = get_engine(name_)
        assert isinstance(instance, _DecoratedEngine)
    finally:
        _ENGINE_REGISTRY.pop(name_, None)


def test_engine_decorator_name_mismatch_raises():
    """@engine("x") on a class with name != "x" raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="must match decorator"):
        @engine("_test_mismatch_name")
        class _MismatchEngine(SemanticEngine):
            name = "_something_else"
            version = "1.0"

            def process(self, document: AIDoc) -> AIDoc:
                return document


# ---------------------------------------------------------------------------
# External engine integration style
# ---------------------------------------------------------------------------


def test_external_engine_style(canonical_document):
    """
    Simulates the external engine package pattern:

        from aidoc_sdk.semantic.decorators import engine
        from aidoc_sdk.semantic.base import SemanticEngine

        @engine("my_domain")
        class MyDomainEngine(SemanticEngine): ...

    The engine must be retrievable by name and produce a valid AIDoc.
    """
    name_ = "_test_external_style"

    try:
        @engine(name_)
        class _ExternalEngine(SemanticEngine):
            name = name_
            version = "2.5"

            def process(self, document: AIDoc) -> AIDoc:
                return document

        instance = get_engine(name_)
        result = instance.process(canonical_document)

        assert result.spec == canonical_document.spec
        assert result.meta.source_hash == canonical_document.meta.source_hash
    finally:
        _ENGINE_REGISTRY.pop(name_, None)
