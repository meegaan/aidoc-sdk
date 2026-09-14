# AIDoc SDK (aidoc-sdk)

AI-native deterministic document canonicalization SDK.

aidoc-sdk is an infrastructure-grade Python SDK that converts unstructured documents into a deterministic, canonical representation suitable for AI systems, enterprise pipelines, auditing, and integrity verification.

## Documentation

| Topic | File |
|---|---|
| Architecture overview | [docs/architecture.md](docs/architecture.md) |
| Extraction system | [docs/extraction.md](docs/extraction.md) |
| Semantic processing | [docs/semantic.md](docs/semantic.md) |
| Structural guardrails | [docs/guardrails.md](docs/guardrails.md) |
| Determinism guarantees | [docs/determinism.md](docs/determinism.md) |
| Extensions & plugins | [docs/extensions.md](docs/extensions.md) |
| Developer guide | [docs/developer-guide.md](docs/developer-guide.md) |
| AIDoc specification | [aidoc-spec/spec.md](aidoc-spec/spec.md) |

## Architecture

aidoc-sdk processes documents through distinct, verifiable layers:

```
File → ExtractorRegistry → BaseExtractor → RawDocument
     → Canonicalization → AIDoc
     → MetadataStage (ProcessorInfo injection)
     → SemanticProcessor → SemanticEngine(s) [opt-in]
```

1. **Extraction**: Pluggable adapters (`txt`, `pdf`, `docx`) auto-detected by file extension via `ExtractorRegistry`. New formats can be added via the `@extractor` decorator or entry-point plugins.
2. **Canonicalization**: Enforces deterministic structure, UTF-8 encoding, and SHA-256 block/section hashing.
3. **Metadata Injection**: Injects `ProcessorInfo` (core version, extractor identity, semantic engine audit trail).
4. **Semantic Enrichment** *(opt-in)*: Extends canonical elements with AI-driven metadata under strict structural guardrails via `SemanticProcessor`. Engines cannot mutate structure.

## Installation

**Core library:**
```bash
pip install aidoc-sdk
```

**Optional capabilities:**
```bash
pip install aidoc-sdk[cli]    # Command-line interface (requires click)
pip install aidoc-sdk[pdf]    # PDF extraction (requires pdfplumber)
pip install aidoc-sdk[docx]   # DOCX extraction (requires python-docx)
```

## Quick Start

```python
from aidoc_sdk import process_file

# Format auto-detected from file extension
doc = process_file("contract.pdf")

print(doc.meta.source_hash)   # SHA-256 of raw input bytes
print(doc.meta.processor)     # Traceability metadata
```

## Semantic Enrichment

Semantic enrichment is **opt-in**. It follows a **Dual-Engine** architecture:

1. **Rule Engine (Deterministic Expert)**: Uses explicit patterns (regex, keywords) to detect structural semantics (Requirements, Prohibitions, Definitions, Conditions, References). It provides deterministic correctness.
2. **LLM Engine (Independent Reasoner)**: Uses probabilistic semantic understanding to classify text even without explicit keywords. It acts as an autonomous classifier, constrained by the SDK's schema.

Both engines output a standardized 8-category taxonomy:
- **Descriptive**: `statement`, `definition`, `reference`
- **Normative**: `requirement`, `prohibition`
- **Procedural**: `instruction`
- **Conditional**: `condition`, `exception`

Enable enrichment explicitly via `PipelineConfig`:

```python
from aidoc_sdk import process_file
from aidoc_sdk.pipeline.config import PipelineConfig
from aidoc_sdk.core.serializer import to_canonical_json

config = PipelineConfig(
    enable_semantic=True,
    semantic_engines=["rule_engine", "llm_engine"]
)

doc = process_file("contract.pdf", config=config)

# Inspect which engines ran, their versions, and any failures
for layer in doc.meta.processor.semantic_layers:
    print(layer.name, layer.version, layer.status)

print(to_canonical_json(doc))
```

### Failure Handling

By default the pipeline fails immediately if an engine errors. For production environments with optional or LLM-based engines, use `continue_on_error` mode:

```python
config = PipelineConfig(
    enable_semantic=True,
    semantic_engines=["rule_engine", "llm_engine"],
    semantic_fail_fast=False   # Log + continue on engine failure
)
```

Failed engines are recorded in `doc.meta.processor.semantic_layers` with `status="failed"` and an `error` message.

## Custom Semantic Engine

Register custom AI/ML or domain-specific engines using the `@engine` decorator. The class `name` attribute **must match** the decorator argument.

```python
from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.semantic.decorators import engine
from aidoc_sdk.core.models import AIDoc

@engine("my_llm_engine")
class MyLLMEngine(SemanticEngine):
    name = "my_llm_engine"   # Must match decorator
    version = "1.0"          # Required — enforced at class definition

    async def process_async(self, document: AIDoc) -> AIDoc:
        # Must return a NEW AIDoc instance — never mutate in place
        return document.model_copy(deep=True)
```

**SDK Control vs. LLM Freedom:** While your engines (especially LLM-based ones) have freedom in reasoning, their output must strictly conform to the `SemanticType` enumeration. This ensures that independent "brains" still produce standardized, verifiable document layers.

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
        # Parse file and return a RawDocument
        ...
```

Built-in extractors (`txt`, `pdf`, `docx`) are loaded automatically via lazy initialization — no manual imports required.

## Async Pipeline

For high-throughput environments (async workers):

```python
from aidoc_sdk.pipeline import Pipeline
from aidoc_sdk.pipeline.config import PipelineConfig, ExecutionMode

pipeline = Pipeline(config=PipelineConfig(
    execution_mode=ExecutionMode.async_mode,
    enable_semantic=True,
    semantic_engines=["rule_engine"]
))

doc = await pipeline.run_async(
    raw_document=raw_document,
    source_hash=source_hash,
    extractor_name="pdf",
    extractor_version="1.0"
)
```

> **Note**: Do **not** call `pipeline.run()` from within a running event loop. Use `pipeline.run_async()` instead.

## CLI

```bash
# Basic processing (format auto-detected from extension)
aidoc-sdk contract.pdf

# With semantic enrichment
aidoc-sdk contract.pdf --semantic

# Explicit format override
aidoc-sdk contract.pdf --format pdf

# Help
aidoc-sdk --help
```

## Error Handling

All SDK errors inherit from `aidoc_sdk.exceptions.AIDocError`:

```python
from aidoc_sdk.exceptions import (
    AIDocError,
    ExtractionError,
    StructuralViolationError,
    EngineExecutionError,
)

try:
    doc = process_file("doc.pdf")
except ExtractionError as e:
    print(f"Extraction failed: {e}")
except EngineExecutionError as e:
    print(f"Semantic engine failed: {e}")
except AIDocError as e:
    print(f"SDK error: {e}")
```

## Public API

The stable public API is exposed through the `aidoc_sdk` package root:

```python
from aidoc_sdk import process_file, Pipeline
```

Internal sub-packages (`core`, `extraction`, `semantic`, `pipeline`) are implementation details and may change between versions. Always import from the package root.

## Design Guarantees

| Property | Guarantee |
|---|---|
| Hashing | SHA-256 of raw input bytes |
| Encoding | UTF-8 strict — invalid inputs raise `DecodeError` |
| Serialization | Deterministic Canonical JSON (sorted keys, no whitespace) |
| Immutability | All models are immutable — stages return new instances |
| Concurrency | Registries are thread-safe for multi-worker deployments |
| Traceability | Full `ProcessorInfo` metadata in every output document |
| Structural Safety | `SemanticProcessor` enforces guardrails — engines cannot mutate structure |
| Lazy Loading | Extractors loaded on first use — no manual imports needed |
