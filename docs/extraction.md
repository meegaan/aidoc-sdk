# Extraction System

## Overview

The extraction layer converts raw files into a `RawDocument`, which is the input to the canonicalization stage.

```
File / Path
    │
    ▼
ExtractorRegistry.for_file(path)
    │   (auto-detects format by file extension)
    ▼
BaseExtractor.extract(path)
    │
    ▼
RawDocument
```

---

## Components

### `BaseExtractor`

Abstract base class for all extractors. Every extractor must define:

```python
from pathlib import Path
from aidoc_sdk.extraction.base import BaseExtractor
from aidoc_sdk.core.raw import RawDocument

class MyExtractor(BaseExtractor):
    name = "my_format"           # Unique extractor identifier
    version = "1.0"              # Version string
    supported_extensions = (".mf",)  # File extensions this extractor handles

    def extract(self, path: Path) -> RawDocument:
        ...
```

- `name` — Unique string identifier used for format-based lookup.
- `version` — Version string recorded in processor metadata.
- `supported_extensions` — Tuple of lowercase extensions (including the dot).
- `extract(path)` — Reads the file and returns a `RawDocument`.

---

### `ExtractorRegistry`

Thread-safe registry mapping file extensions to extractor classes.

**Key methods:**

| Method | Description |
|---|---|
| `registry.for_file(path)` | Auto-detect format by extension and return an extractor instance |
| `registry.get_by_format(name)` | Lookup by explicit format name (e.g. `"pdf"`) |
| `registry.get_by_extension(ext)` | Lookup by raw extension string (e.g. `".pdf"`) |
| `registry.register(cls)` | Manually register an extractor class |
| `registry.list_extractors()` | List all registered extractor names |

**Extension collision protection:** If two extractors claim the same extension, `ExtractorConflictError` is raised immediately at registration time — no silent overwrite.

---

### `ExtractorLoader` (`loader.py`)

Invoked automatically by the registry on first use (lazy initialization). It:

1. Imports built-in extractor modules to trigger `@extractor` decorator registration.
2. Calls `registry.load_plugins()` to discover external extractors via `importlib.metadata` entry points.

Users never need to call this directly.

---

## Lazy Initialization

The `ExtractorRegistry` uses a **thread-safe double-checked locking pattern**:

```python
registry = ExtractorRegistry()

# First call triggers lazy load transparently
extractor = registry.for_file("contract.pdf")  # loads built-ins + plugins first
```

This guarantees extractors are always available without forcing eager imports at SDK startup.

---

## Supported Formats

| Format | Class | Optional Dependency |
|---|---|---|
| Plain text (`.txt`) | `TxtExtractor` | None |
| PDF (`.pdf`) | `PdfExtractor` | `pdfplumber` (`pip install aidoc-sdk[pdf]`) |
| Word document (`.docx`) | `DocxExtractor` | `python-docx` (`pip install aidoc-sdk[docx]`) |

---

## `RawDocument`

The output of extraction. It is a structured but un-canonicalized representation:

- `sections` — List of raw sections with title, level, and raw text/table data
- `source_hash` — SHA-256 of the original input bytes (frozen at extraction time)

---

## Custom Extractor Example

```python
from pathlib import Path
from aidoc_sdk.extraction.base import BaseExtractor
from aidoc_sdk.extraction.registry import extractor
from aidoc_sdk.core.raw import RawDocument

@extractor("xml")
class XMLExtractor(BaseExtractor):
    name = "xml"
    version = "1.0"
    supported_extensions = (".xml",)

    def extract(self, path: Path) -> RawDocument:
        # Read and parse your format, return RawDocument
        ...
```

See [extensions.md](extensions.md) for plugin registration via entry points.
