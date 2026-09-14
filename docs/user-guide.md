# User Guide

## Basic Usage

The recommended entry point is `process_file`. It reads the file, detects the format automatically, extracts, hashes, and canonicalizes in a single call.

```python
from aidoc_sdk import process_file

# Format auto-detected from file extension
doc = process_file("contract.pdf")

print(doc.meta.source_hash)   # SHA-256 fingerprint of raw input
print(doc.spec)                # e.g. "aidoc@1.0"
```

## Semantic Enrichment

Semantic enrichment is **disabled by default**. It classifies document blocks into 8 standardized categories: Requirement, Prohibition, Instruction, Condition, Exception, Statement, Definition, and Reference.

Opt-in via `PipelineConfig`:

```python
from aidoc_sdk import process_file
from aidoc_sdk.pipeline.config import PipelineConfig

config = PipelineConfig(
    enable_semantic=True,
    semantic_engines=["rule_engine", "llm_engine"]
)

doc = process_file("contract.pdf", config=config)

# Traceability: shows which engines ran, their versions, and execution status
for layer in doc.meta.processor.semantic_layers:
    print(layer.name, layer.version, layer.status)
```

### Continue-On-Error Mode

For production environments using optional or unreliable engines (e.g. LLM endpoints), set `semantic_fail_fast=False`. The pipeline will log failures and continue:

```python
config = PipelineConfig(
    enable_semantic=True,
    semantic_engines=["rule_engine", "llm_engine"],
    semantic_fail_fast=False
)

doc = process_file("contract.pdf", config=config)

# Inspect failures
for layer in doc.meta.processor.semantic_layers:
    if layer.status == "failed":
        print(f"{layer.name} failed: {layer.error}")
```

## Async Execution

For async workers or high-throughput pipelines:

```python
from aidoc_sdk.pipeline import Pipeline
from aidoc_sdk.pipeline.config import PipelineConfig

pipeline = Pipeline(config=PipelineConfig(
    enable_semantic=True,
    semantic_engines=["rule_engine"]
))

# Always use run_async() inside an event loop
doc = await pipeline.run_async(
    raw_document=raw_document,
    source_hash=source_hash,
    extractor_name="pdf",
    extractor_version="1.0"
)
```

> **Important**: Do not call `pipeline.run()` from within a running event loop. Use `run_async()` inside async contexts.

## Deterministic Fingerprinting

```python
from aidoc_sdk.core.serializer import to_canonical_bytes
from aidoc_sdk.core.hashing import hash_canonical_json

canonical_bytes = to_canonical_bytes(doc)
fingerprint = hash_canonical_json(canonical_bytes)
```

## Custom Semantic Engine

```python
from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.semantic.decorators import engine
from aidoc_sdk.core.models import AIDoc

@engine("my_engine")
class MyEngine(SemanticEngine):
    name = "my_engine"   # Must exactly match the decorator argument
    version = "1.0"      # Required — missing version raises TypeError at import time

    def process(self, document: AIDoc) -> AIDoc:
        # Must return a NEW AIDoc — never mutate the input
        return document.model_copy(deep=True)

    async def process_async(self, document: AIDoc) -> AIDoc:
        # Override for native async processing
        return self.process(document)
```

## External Domain Engines

You can create standalone packages containing domain-specific logic without modifying aidoc-sdk Core.

**Example: `aidoc_legal/engine.py`**
```python
from aidoc_sdk.semantic.decorators import engine
from aidoc_sdk.semantic.base import SemanticEngine

@engine("legal")
class LegalEngine(SemanticEngine):
    name = "legal"
    version = "1.0"

    def process(self, document):
        # Implementation...
        return document
```

Users install and enable your package:
```python
import aidoc_legal  # Triggers decorator registration

config = PipelineConfig(
    enable_semantic=True,
    semantic_engines=["legal"]
)
```

Alternatively, register via `pyproject.toml` entry points (no import needed):
```toml
[project.entry-points."aidoc_sdk.extractors"]
legal = "aidoc_legal.engine:LegalEngine"
```

## Custom Extractor

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
        # Parse raw file and return a RawDocument
        ...
```

The `ExtractorRegistry` loads built-in and plugin extractors automatically on first use — no manual imports required.

## CLI Reference

```bash
# Process a document (format auto-detected)
aidoc-sdk contract.pdf

# With semantic enrichment
aidoc-sdk contract.pdf --semantic

# Explicit format override
aidoc-sdk contract.pdf --format pdf

# Help
aidoc-sdk --help
```

**Supported formats:** `txt`, `pdf` (requires `aidoc-sdk[pdf]`), `docx` (requires `aidoc-sdk[docx]`)

## Error Handling

```python
from aidoc_sdk.exceptions import (
    AIDocError,              # Root — catch-all
    ExtractionError,         # Adapter failed
    EngineExecutionError,    # Semantic engine failed (fail_fast=True)
    StructuralViolationError,# Engine mutated document structure
    DecodeError,             # Invalid UTF-8 input
    ConfigurationError,      # Invalid engine/extractor registration
)

try:
    doc = process_file("doc.pdf")
except ExtractionError as e:
    ...  # Format-specific failure
except EngineExecutionError as e:
    ...  # Engine crash in fail-fast mode
except AIDocError as e:
    ...  # Any SDK error
```
