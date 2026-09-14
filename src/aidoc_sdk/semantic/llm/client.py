"""
LLM Client Abstraction
======================

Provides isolated async interface for calling external LLM providers.

Design Principles:

- Fully isolated from core models
- No canonical schema dependency
- No semantic conversion logic
- Async-first
- Provider-agnostic
- Deterministic core remains unaffected

This module handles transport only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from aidoc_sdk.exceptions import SemanticError


# ============================================================================
# BASE CLIENT
# ============================================================================


class BaseLLMClient(ABC):
    """
    Abstract LLM transport client.
    """

    name: str

    @abstractmethod
    async def generate(self, prompt: str) -> Dict[str, Any]:
        """
        Send prompt to LLM provider and return raw JSON response.

        Must return parsed JSON (dict).
        Must NOT return string.
        """
        ...


# ============================================================================
# GENERIC HTTP CLIENT (PROVIDER-AGNOSTIC EXAMPLE)
# ============================================================================


class HTTPJSONLLMClient(BaseLLMClient):
    """
    Generic async HTTP JSON client for LLM APIs.

    This is provider-agnostic.
    Concrete provider configs must supply:
        - endpoint
        - headers
        - request body structure
    """

    def __init__(
        self,
        name: str,
        endpoint: str,
        headers: Dict[str, str],
        timeout: float = 30.0,
    ) -> None:
        self.name = name
        self._endpoint = endpoint
        self._headers = headers
        self._timeout = timeout

    async def generate(self, prompt: str) -> Dict[str, Any]:
        try:
            import httpx
        except ImportError as exc:
            raise SemanticError("httpx is required for HTTPJSONLLMClient") from exc

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._endpoint,
                headers=self._headers,
                json={"prompt": prompt},
            )

        if response.status_code != 200:
            raise SemanticError(
                f"LLM request failed: {response.status_code}"
            )

        try:
            return response.json()
        except Exception as exc:
            raise SemanticError("Invalid JSON response from LLM") from exc
