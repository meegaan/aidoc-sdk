"""
AIDoc Interfaces Package
========================

Public-facing integration surface for AIDoc SDK.

Exposes:

- process_file
- process_bytes

CLI entrypoint is intentionally not auto-imported.
"""

from aidoc_sdk.interfaces.api import (
    process_file,
    process_bytes,
)

__all__ = [
    "process_file",
    "process_bytes",
]
