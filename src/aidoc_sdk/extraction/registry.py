"""
Extraction Registry
-------------------

Central registry for extraction adapters.

Supports:

- Explicit registration
- Lookup by format
- Lookup by file extension
- Future plugin discovery (entry-points ready)

Extraction adapters must subclass BaseExtractor.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Dict, Type
import importlib.metadata

from aidoc_sdk.extraction.base import BaseExtractor
from aidoc_sdk.exceptions import ConfigurationError, ExtractorConflictError

logger = logging.getLogger(__name__)


class ExtractorRegistry:
    def __init__(self):
        self._extractors: Dict[str, Type[BaseExtractor]] = {}
        self._extension_map: Dict[str, Type[BaseExtractor]] = {}
        self._lock = threading.Lock()
        self._initialized = False

    def _ensure_loaded(self) -> None:
        """Guarantee built-ins and plugins are fully registered before lookup (Lazy Load)."""
        if self._initialized:
            return
            
        with self._lock:
            # Double-checked locking pattern
            if self._initialized: return
            
            # 1. Load Built-ins
            from aidoc_sdk.extraction.loader import load_builtins
            load_builtins()
            
            # 2. Discover Plugins
            self.load_plugins()
            
            self._initialized = True

    def register(self, extractor_cls: Type[BaseExtractor]) -> None:
        """Register an extractor class."""
        if not issubclass(extractor_cls, BaseExtractor):
            raise ConfigurationError("Extractor must subclass BaseExtractor")

        with self._lock:
            if extractor_cls.name in self._extractors:
                raise ConfigurationError(f"Extractor already registered for '{extractor_cls.name}'")

            # Check for extension collisions BEFORE committing any changes
            for ext in getattr(extractor_cls, "supported_extensions", []):
                norm_ext = ext.lower().lstrip(".")
                if norm_ext in self._extension_map:
                    existing = self._extension_map[norm_ext]
                    raise ExtractorConflictError(
                        f"Extension '.{norm_ext}' is already registered by "
                        f"'{existing.name}'. Cannot register '{extractor_cls.name}'."
                    )

            # Commit only after all collision checks pass
            self._extractors[extractor_cls.name] = extractor_cls
            for ext in getattr(extractor_cls, "supported_extensions", []):
                norm_ext = ext.lower().lstrip(".")
                self._extension_map[norm_ext] = extractor_cls

    def get_by_format(self, format_name: str) -> BaseExtractor:
        """Lookup by the explicit extractor name."""
        self._ensure_loaded()
        extractor_cls = self._extractors.get(format_name)
        if not extractor_cls:
            raise ConfigurationError(f"No extractor registered for '{format_name}'")
        return extractor_cls()

    def get_by_extension(self, ext: str) -> BaseExtractor:
        """Lookup by file extension."""
        self._ensure_loaded()
        norm_ext = ext.lower().lstrip(".")
        extractor_cls = self._extension_map.get(norm_ext)
        if not extractor_cls:
            raise ConfigurationError(f"No extractor registered for extension '.{norm_ext}'")
        return extractor_cls()

    def for_file(self, path: str | Path) -> BaseExtractor:
        """Lookup the appropriate extractor for a given file path."""
        path = Path(path)
        return self.get_by_extension(path.suffix)
        
    def list_extractors(self) -> list[str]:
        self._ensure_loaded()
        return list(self._extractors.keys())

    def load_plugins(self):
        """Automatically load extractors from entry points."""
        try:
            # For Python 3.10+
            endpoints = importlib.metadata.entry_points(group="aidoc_sdk.extractors")
        except TypeError:
            # Fallback for older python
            endpoints = importlib.metadata.entry_points().get("aidoc_sdk.extractors", [])
            
        for entry_point in endpoints:
            try:
                extractor_cls = entry_point.load()
                self.register(extractor_cls)
            except Exception as e:
                logger.warning(f"Failed to load extraction plugin {entry_point.name}: {e}")

# Global singleton
registry = ExtractorRegistry()

# ---------------------------------------------------------
# Backwards Compability Hooks
# ---------------------------------------------------------

def register_extractor(format_name: str, extractor_cls: Type[BaseExtractor]) -> None:
    # We ignore format_name here since the class should define its own `name`
    # and registry enforces extracting it from the class. We just pass it through.
    registry.register(extractor_cls)


def extractor(format_name: str):
    """
    Decorator to register an extractor class.
    
    Example:
        @extractor("txt")
        class TxtExtractor(BaseExtractor):
            ...
    """
    def wrapper(cls: Type[BaseExtractor]):
        register_extractor(format_name, cls)
        return cls
    return wrapper


def get_extractor(format_name: str) -> BaseExtractor:
    return registry.get_by_format(format_name)


def list_extractors() -> list[str]:
    return registry.list_extractors()

