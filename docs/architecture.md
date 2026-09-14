# AIDoc SDK — Architecture Overview

## Pipeline Diagram

```
┌──────────────────────────────────────────────────────────┐
│                         Input                            │
│                   File / Bytes / Path                    │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                  Extraction Stage                        │
│  ExtractionStage  →  Registry  →  RawDocument            │
│  (receives path/bytes from context; detects format)      │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│             Core Canonicalization Layer                   │
│   CanonicalStage  →  Normalizer  →  AIDoc                │
│   (SHA-256 block/section IDs, UTF-8, deterministic JSON) │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│               Metadata Injection Layer                    │
│   MetadataStage  →  ProcessorInfo injected into AIDoc    │
│   (core version, extractor identity, semantic audit log) │
└────────────────────────┬─────────────────────────────────┘
                         │ (opt-in only)
                         ▼
┌──────────────────────────────────────────────────────────┐
│             Semantic Processing Layer                     │
│   SemanticProcessor  →  SemanticEngine(s)                │
│   (structural guardrails enforced per engine call)       │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
                      AIDoc
              (immutable canonical output)
```

---

## Layers

### 1. Extraction Stage

This is the first component in the pipeline. It converts raw input (file path or bytes) from the `PipelineContext` into a `RawDocument`.

- **`ExtractionStage`** — The formal pipeline component that triggers the registry.
- **`ExtractorRegistry`** — Thread-safe registry mapping extensions to extractors.
- **`BaseExtractor`** — The unit of extraction logic.

This stage is responsible for:
1. Detecting the correct extractor (by extension or explicit name).
2. Computing the source SHA-256 hash.
3. Converting binary content into the structured `RawDocument`.

See [extraction.md](extraction.md) for details.

---

### 2. Core Canonicalization Layer

Converts `RawDocument` into an immutable `AIDoc`.

- Normalizes text (UTF-8, whitespace)
- Assigns deterministic SHA-256 IDs to every section and block
- Freezes structure — no further structural changes are permitted

This layer is **fully deterministic**: identical inputs always produce identical `AIDoc` outputs.

See [determinism.md](determinism.md) for details.

---

### 3. Metadata Injection Layer

Injects `ProcessorInfo` into the `AIDoc` meta field.

`ProcessorInfo` records:
- `aidoc_core` — SDK core version
- `extractor` — Name and version of the extractor used
- `semantic_layers` — Audit list of semantic engine results (populated later)

This stage runs **after** canonicalization and **before** semantic processing.

---

### 4. Semantic Processing Layer

Enriches the canonical `AIDoc` with machine-readable meaning. Entirely opt-in.

- **`SemanticProcessor`** — Orchestrates sequential engine execution. Enforces structural guardrails after each engine call.
- **`SemanticEngine`** — Abstract interface. Engines implement `process(doc) -> AIDoc`.
- **Dual-Engine Architecture:**
    - `RuleEngine`: Deterministic expert logic using regex patterns for high-precision extraction.
    - `LLMEngine`: Independent semantic reasoning for context-aware classification.

Engines may only modify `block.semantic` and must conform to the 8-category standardized taxonomy (`requirement`, `prohibition`, etc.). They cannot alter `id`, `text`, section structure, `spec`, or `source_hash`.

See [semantic.md](semantic.md) and [guardrails.md](guardrails.md) for details.

---

### 5. Interfaces / Public API Layer

The `aidoc_sdk` package exposes a stable public surface:

```python
from aidoc_sdk import process_file, process_bytes, Pipeline, PipelineConfig
```

These high-level functions orchestrate the full pipeline. Users do not need to interact with individual stages.

---

## Design Principles

| Principle | How It's Enforced |
|---|---|
| **Immutability** | All `AIDoc` models are Pydantic frozen models |
| **Determinism** | SHA-256 IDs, canonical JSON, no runtime entropy in core |
| **Separation of concerns** | Each layer is isolated; semantic cannot alter core |
| **Extensibility** | `@extractor` and `@engine` decorators + entry-point plugins |
| **Thread safety** | Registries protected by `threading.Lock` |
| **Structural integrity** | `SemanticProcessor` enforces fingerprint-based guardrails |
