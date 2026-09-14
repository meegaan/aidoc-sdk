"""
Semantic Engine Contract
========================

Defines the enrichment engine interface.

Design Rules:

- Engine MUST return a new AIDoc instance
- Engine MUST NOT mutate input document
- Engine MUST NOT modify structure
- Engine MUST NOT modify spec or source_hash
- Engine MAY enrich block.semantic
- Engine MAY append processor.semantic_layers
- Engine MUST declare name and version
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from aidoc_sdk.core.models import AIDoc


class SemanticEngine(ABC):
    """
    Abstract base class for semantic enrichment engines.

    Every concrete subclass must declare:

    - ``name: str`` — unique engine identifier (matched by ``@engine`` decorator)
    - ``version: str`` — semantic version string (e.g. '1.0')

    Failure to declare either raises ``TypeError`` at class definition time.
    """

    name: str
    version: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Skip enforcement on abstract intermediates
        if ABC in cls.__mro__[1:]:
            return
        if not getattr(cls, "version", None):
            raise TypeError(
                f"SemanticEngine subclass '{cls.__name__}' must define 'version = ...' "
                "as a class attribute."
            )

    @abstractmethod
    def process(self, document: AIDoc) -> AIDoc:
        """
        Perform semantic enrichment.

        Must return a NEW AIDoc instance.
        """
        ...

    async def process_async(self, document: AIDoc) -> AIDoc:
        """
        Perform semantic enrichment asynchronously.
        
        Default implementation falls back to synchronous execution.
        Must return a NEW AIDoc instance.
        """
        return self.process(document)
