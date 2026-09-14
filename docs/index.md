# aidoc-sdk Architecture

aidoc-sdk is designed for deterministic document canonicalization. It converts unstructured files into immutable, canonical forms suitable for AI pipelines, auditing, and integrity verification.

> [!IMPORTANT]
> **Enterprise Documentation Strategy**
> For the complete, architect-level master reference guide containing the full specification and deep technical internals in a single document, please refer to the [Master Reference Manual (HTML)](aidoc-developer-guide.html).

## Pipeline Stages

Documents are processed through strict, verifiable stages:

```
File
 └─ ExtractorRegistry (auto-detects format by extension)
     └─ BaseExtractor → RawDocument
         └─ CanonicalStage → AIDoc
             └─ MetadataStage (injects ProcessorInfo)
                 └─ SemanticStage [opt-in]
                     └─ SemanticProcessor
                         └─ SemanticEngine(s)
```

| Stage | Responsibility |
|---|---|
| **Extraction** | `ExtractorRegistry` selects the correct `BaseExtractor` by file extension. Adapters convert raw bytes to a `RawDocument`. Built-in formats: `txt`, `pdf`, `docx`. |
| **Canonicalization** | Normalizes, hashes, and structures elements into an immutable `AIDoc` with SHA-256 block/section IDs. |
| **Metadata Injection** | Injects `ProcessorInfo` (core version, extractor identity, semantic layer audit list). |
| **Semantic Enrichment** | Optional AI enrichment via `SemanticProcessor` with structural guardrails. Engines may only modify `block.semantic`. |

## Core Guarantees

| Property | Guarantee |
|---|---|
| Hashing | SHA-256 of raw input bytes — frozen after extraction |
| Encoding | UTF-8 strict — invalid input raises `DecodeError` |
| Serialization | Deterministic Canonical JSON (sorted keys, no whitespace) |
| Immutability | All models are immutable — stages produce new instances |
| Concurrency | Registries protected by `threading.Lock` for Gunicorn/Celery safety |
| Traceability | `ProcessorInfo` records core version, extractor, and all semantic layers with `status` and `error` |

## ExtractorRegistry & Lazy Loading

Extractors register themselves via the `@extractor` decorator. The `ExtractorRegistry` uses **Thread-Safe Lazy Initialization** — built-in extractors and entry-point plugins are loaded automatically on first use. No manual imports are required.

External extractor packages can register via `pyproject.toml` entry points:

```toml
[project.entry-points."aidoc_sdk.extractors"]
ocr = "my_pkg.extractor:OCRExtractor"
```

## Semantic Engine Guardrails & Extensibility

All engines execute inside `SemanticProcessor`, which enforces:

- Engine **cannot** modify `spec`, `source_hash`, or block structure
- Engine **must** return a new `AIDoc` instance (no in-place mutation)
- Guardrail violations are wrapped as `EngineExecutionError`
- `ProcessorInfo` is injected by `MetadataStage` **before** enrichment begins
- `version` must be declared on every engine class (enforced at import time)
- Engines are registered via the `@engine` decorator from `aidoc_sdk.semantic.decorators`
- `semantic_fail_fast=False` enables continue-on-error mode for resilient production pipelines

## Semantic Layer Metadata

Each engine run appends a `SemanticLayerInfo` record to `doc.meta.processor.semantic_layers`:

```json
{
  "name": "rule_engine",
  "version": "1.0",
  "status": "success",
  "error": null
}
```

When an engine fails in continue-on-error mode:

```json
{
  "name": "llm_engine",
  "version": "1.0",
  "status": "failed",
  "error": "ConnectTimeout: API unreachable"
}
```

## Concurrency Model

The sync `Pipeline.run()` and async `Pipeline.run_async()` share the same stage graph. Async-only stages raise `NotImplementedError` when called synchronously with a clear message, preventing silent event loop issues.
