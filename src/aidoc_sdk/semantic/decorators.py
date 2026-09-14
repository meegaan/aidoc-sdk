"""
Semantic Engine Decorator
=========================

Public import path for the ``@engine`` registration decorator.

This module exists as a stable, dedicated import surface so that external
engine packages can depend on a fixed path without coupling to registry
internals::

    from aidoc_sdk.semantic.decorators import engine

    @engine("legal")
    class LegalEngine(SemanticEngine):
        name = "legal"
        version = "1.0"

        def process(self, document: AIDoc) -> AIDoc:
            ...

Design Note:
    The decorator itself lives in ``semantic/registry.py`` to avoid a
    circular import (registry imports base; decorators would import
    registry).  This module is a deliberate re-export shim — its only job
    is to provide the canonical public path.
"""

from __future__ import annotations

from aidoc_sdk.semantic.registry import engine

__all__ = ["engine"]
