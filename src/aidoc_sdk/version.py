from __future__ import annotations

"""
AIDoc Framework Version
=======================

Single source of truth for the SDK package version.

Follows Semantic Versioning (MAJOR.MINOR.PATCH).

MAJOR:
    Breaking public API or canonical schema change
MINOR:
    Backward-compatible feature additions
PATCH:
    Backward-compatible bug fixes
"""

from typing import Final

__version__: Final[str] = "1.0.0"


def get_version() -> str:
    return __version__


__all__ = ["__version__", "get_version"]
