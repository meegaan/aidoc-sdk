"""
Semantic Engine Registry
========================

Central registry for semantic enrichment engines.

Design Principles:

- Explicit registration only
- No implicit side-effects
- No auto-discovery by default
- Engine identity = name (unique)
- Registry stores engine classes, not instances
- Instance creation is controlled

Changing registry behavior does NOT affect structural contract.
"""

from __future__ import annotations

import threading
from typing import Dict, Type, List

from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.exceptions import ConfigurationError


def engine(name: str):
    """
    Decorator for declarative semantic engine registration.

    The class must define ``name = '<name>'`` matching the decorator argument.
    Raises ConfigurationError if the name does not match or is missing.

    Example::

        @engine("rule_engine")
        class RuleEngine(SemanticEngine):
            name = "rule_engine"
            version = "1.0"
    """
    def decorator(cls: Type[SemanticEngine]) -> Type[SemanticEngine]:
        cls_name = getattr(cls, "name", None)
        if cls_name != name:
            raise ConfigurationError(
                f"Engine class '{cls.__name__}.name' must match decorator: "
                f"expected '{name}', got '{cls_name}'."
            )
        register_engine(cls)
        return cls
    return decorator


# ============================================================================
# INTERNAL REGISTRY STORAGE
# ============================================================================

_ENGINE_REGISTRY: Dict[str, Type[SemanticEngine]] = {}
_REGISTRY_LOCK = threading.Lock()


# ============================================================================
# REGISTRATION
# ============================================================================


def register_engine(engine_cls: Type[SemanticEngine]) -> None:
    """
    Register a semantic engine class.

    Engine class must define:
        - name (unique)
        - version
    """

    if not issubclass(engine_cls, SemanticEngine):
        raise ConfigurationError(
            "Engine must subclass SemanticEngine"
        )

    name = getattr(engine_cls, "name", None)

    if not name or not isinstance(name, str):
        raise ConfigurationError(
            "Engine must define a non-empty string 'name'"
        )

    if name in _ENGINE_REGISTRY:
        raise ConfigurationError(
            f"Engine '{name}' already registered"
        )

    with _REGISTRY_LOCK:
        _ENGINE_REGISTRY[name] = engine_cls


# ============================================================================
# RETRIEVAL
# ============================================================================


def get_engine(name: str) -> SemanticEngine:
    """
    Instantiate registered engine by name.
    """

    engine_cls = _ENGINE_REGISTRY.get(name)

    if engine_cls is None:
        raise ConfigurationError(
            f"No semantic engine registered under '{name}'"
        )

    return engine_cls()


def list_engines() -> List[str]:
    """
    List registered engine names.
    """

    return list(_ENGINE_REGISTRY.keys())
