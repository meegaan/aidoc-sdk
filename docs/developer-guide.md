# Developer Guide

## Project Overview

AIDoc SDK is an infrastructure-grade Python SDK that converts unstructured documents into a deterministic, canonical format (AIDoc) suitable for AI pipelines, auditing, and integrity verification.

## Public API Boundary

The **stable public API** is everything exported via `aidoc_sdk.__all__`:

```python
# These are stable — safe for external users
from aidoc_sdk import (
    process_file, process_bytes,
    Pipeline, PipelineConfig, ExecutionMode,
    AIDoc,
    structural_fingerprint, full_document_fingerprint,
    SemanticEngine, RuleEngine, LLMEngine,
    AIDocError, ExtractionError, ExtractorConflictError,
    EngineExecutionError, ...
)
```

The following sub-packages are **internal implementation details** and may change between versions:
- `aidoc_sdk.core.*`
- `aidoc_sdk.extraction.*` (except via `process_file`)
- `aidoc_sdk.semantic.processor`, `aidoc_sdk.semantic.registry`
- `aidoc_sdk.pipeline.stages`, `aidoc_sdk.pipeline.context`

> As a **contributor**, you may import from internal modules freely. As a **user**, only import from the package root.

**Repository layout:**

```
src/aidoc_sdk/
├── core/           # Canonical data models, fingerprinting, guardrails, serialization
├── extraction/     # BaseExtractor, ExtractorRegistry, built-in format adapters
├── semantic/       # SemanticProcessor, engine interface, built-in engines
├── pipeline/       # Pipeline orchestration, stage definitions, config
├── interfaces/     # High-level public API (process_file, process_bytes)
└── exceptions.py   # Full exception hierarchy

docs/               # Markdown documentation
aidoc-spec/         # Language-independent AIDoc specification + JSON Schema
tests/
├── unit/           # Fast, isolated unit tests
└── debug/          # Ad-hoc debug scripts (not part of test suite)
```

---

## Setup

```bash
# Create and activate virtual environment
uv venv && .\.venv\Scripts\activate   # Windows
# or: python -m venv .venv && source .venv/bin/activate

# Install with all optional dependencies
uv pip install -e ".[pdf,docx,cli]"

# Run the test suite
uv run pytest
```

---

## Architecture

See [architecture.md](architecture.md) for the full pipeline diagram.

At a high level:

```
File → Extraction → RawDocument → Canonicalization → AIDoc → Semantic [opt-in]
```

The core pipeline is deterministic. Semantic engines are opt-in and non-destructive.

---

## Adding a New Extractor

1. Create a new module under `src/aidoc_sdk/extraction/<format>/extractor.py`.
2. Subclass `BaseExtractor` and declare `name`, `version`, `supported_extensions`.
3. Implement `extract(self, path: Path) -> RawDocument`.
4. Apply the `@extractor` decorator with the format name.
5. Add a guarded import to `src/aidoc_sdk/extraction/loader.py` inside `load_builtins()`.

```python
# loader.py
def load_builtins() -> None:
    from aidoc_sdk.extraction.txt import TxtExtractor  # noqa
    try:
        from aidoc_sdk.extraction.pdf.extractor import PdfExtractor  # noqa
    except ImportError:
        pass
    try:
        from aidoc_sdk.extraction.myformat.extractor import MyExtractor  # noqa
    except ImportError:
        pass
```

6. Add unit tests in `tests/unit/extraction/`.

---

## Adding a New Semantic Engine

1. Create `src/aidoc_sdk/semantic/<name>/engine.py`.
2. Subclass `SemanticEngine`, declare `name` and `version`, implement `process()`.
3. Apply the `@engine` decorator.
4. Add unit tests in `tests/unit/semantic/`.

**Engine contract (must pass before merging):**
- Returns new `AIDoc` — never mutates input
- Only modifies `block.semantic` using the standardized 8-category taxonomy
- Structural fingerprint before == after
- `process_async` is implemented or inherits the sync fallback

> **Note**: When implementing the `exception` semantic type, use the `LogicException` model to avoid shadowing Python's built-in `Exception` class.

---

## Adding a New Pipeline Stage
 
 1. Create a new subclass of `PipelineStage` in `src/aidoc_sdk/pipeline/stages.py` (or a separate module).
 2. Implement the `execute(self, context: PipelineContext) -> PipelineContext` method.
 3. Use `context.replace(**updates)` to return a new context instance with your modifications.
 4. (Optional) Implement `execute_async()` if the stage requires specialized async behavior.
 
 ```python
 class MyCustomStage(PipelineStage):
     name = "custom_stage"
 
     def execute(self, context: PipelineContext) -> PipelineContext:
         # Stages should pull from context and return a new context
         doc = context.canonical_document
         # ... perform work ...
         return context.replace(canonical_document=new_doc)
 ```
 
 5. Add the stage to the stage list in `Pipeline._build_stages()`.
 
 ---
 
 ## Adding a New Exception

Add to `src/aidoc_sdk/exceptions.py` under the appropriate section. Add the new class to `__all__`. Export it from `src/aidoc_sdk/__init__.py`.

> Adding a new exception is a **MINOR** change. Removing or renaming is **MAJOR** (breaking).

---

## Testing Guidelines

```bash
# Run full suite
uv run pytest

# Run a single file
uv run pytest tests/unit/semantic/test_semantic_processor.py -v

# Run with output on failure
uv run pytest --tb=short
```

**Test structure:**
- `tests/unit/` — One file per module. Use fixtures from `conftest.py`.
- Tests must not rely on external APIs, files, or network.
- Each semantic engine test should verify the structural fingerprint is unchanged after processing.

**Guardrail tests:**
Any new semantic engine should include a test that attempts structural mutation and asserts `EngineExecutionError` is raised:

```python
def test_engine_cannot_mutate_structure(canonical_document):
    doc = _with_processor(canonical_document)
    processor = SemanticProcessor([MaliciousEngine()])
    with pytest.raises(EngineExecutionError):
        processor.process(doc)
```

---

## Key Design Rules

1. **Never mutate models in-place.** Use `.model_copy(update={...})` to produce new instances.
2. **Never add randomness or timestamps to structural layers.** These must be deterministic.
3. **Semantic engines must not import from pipeline internals.** They should only depend on `aidoc_sdk.core.models` and `aidoc_sdk.semantic.base`.
4. **All public exceptions must inherit from `AIDocError`.** No raw Python exceptions should propagate past SDK boundaries.
5. **Registries are thread-safe.** Use the existing `threading.Lock` pattern; do not bypass it.

---

## Specification

The `aidoc-spec/` directory contains the language-independent AIDoc specification:

- `spec.md` — Human-readable normative specification
- `aidoc-1.0.schema.json` — JSON Schema for document validation

When adding new fields to `SemanticLayerInfo`, `ProcessorInfo`, or any structural model, regenerate the schema:

```bash
uv run python -c "
from aidoc_sdk.core.models import AIDoc
import json
schema = AIDoc.model_json_schema()
schema['$schema'] = 'http://json-schema.org/draft-07/schema#'
schema['$id'] = 'https://aidoc.dev/schema/aidoc-1.0.schema.json'
open('aidoc-spec/aidoc-1.0.schema.json', 'w').write(json.dumps(schema, indent=2))
"
```
