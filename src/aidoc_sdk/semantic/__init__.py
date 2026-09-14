"""
AIDoc Semantic Package
======================

Pluggable semantic enrichment layer.

Public Surface:

- SemanticEngine (base contract)
- engine (registration decorator)
- SemanticProcessor (guarded executor)
- register_engine / get_engine / list_engines
- RuleEngine (deterministic engine)
- LLMEngine (async LLM-based engine)

Internal modules (schema, client internals) are intentionally hidden.
"""

from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.semantic.decorators import engine
from aidoc_sdk.semantic.processor import SemanticProcessor
from aidoc_sdk.semantic.registry import (
    register_engine,
    get_engine,
    list_engines,
)
from aidoc_sdk.semantic.rule_engine import RuleEngine
from aidoc_sdk.semantic.llm.engine import LLMEngine

__all__ = [
    "SemanticEngine",
    "engine",
    "SemanticProcessor",
    "register_engine",
    "get_engine",
    "list_engines",
    "RuleEngine",
    "LLMEngine",
]
