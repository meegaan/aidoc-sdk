from __future__ import annotations

"""
AIDoc Core Version Governance
=============================

Defines canonical and deterministic contract versions.

Scope of this module:

- Governs canonical document schema version
- Governs deterministic processing contract version
- Does NOT define framework/package version

Design Principles:

- Deterministic core must remain stable
- Structural schema changes are strictly governed
- Semantic enrichment does NOT affect structural versioning
- Version constants are immutable at runtime
- No side effects
- No framework lifecycle logic

Versioning Rules:

1. SPEC_VERSION:
   - Represents canonical document schema contract.
   - Any structural change to AIDoc models requires MAJOR SDK bump.

2. CORE_CONTRACT_VERSION:
   - Represents deterministic processing contract:
       - normalization
       - hashing
       - canonicalization
       - serialization
       - structural fingerprint rules
   - Any behavioral change requires MAJOR SDK bump.

Compatibility Policy:

- Enrichment features DO NOT change SPEC_VERSION.
- Processor metadata changes DO NOT affect structural fingerprint.
- Hashing algorithm change REQUIRES MAJOR bump.
- Canonical JSON format change REQUIRES MAJOR bump.
"""

from typing import Final


# ============================================================================
# CANONICAL SPECIFICATION VERSION
# ============================================================================

SPEC_VERSION: Final[str] = "aidoc@1.0"


# ============================================================================
# DETERMINISTIC CORE CONTRACT VERSION
# ============================================================================

CORE_CONTRACT_VERSION: Final[str] = "1.0"


# ============================================================================
# PUBLIC ACCESSORS
# ============================================================================


def get_spec_version() -> str:
    """Return canonical document specification version."""
    return SPEC_VERSION


def get_core_contract_version() -> str:
    """Return deterministic core processing contract version."""
    return CORE_CONTRACT_VERSION


__all__ = [
    "SPEC_VERSION",
    "CORE_CONTRACT_VERSION",
    "get_spec_version",
    "get_core_contract_version",
]
