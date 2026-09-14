# Semantic Processing

## Overview

The semantic layer enriches the canonical `AIDoc` with machine-readable meaning. It is **entirely opt-in** and runs after core canonicalization.

```
AIDoc (canonical, immutable)
    │
    ▼
SemanticProcessor
    │  (wraps each engine call with structural guardrails)
    ├─ SemanticEngine 1  (e.g. RuleEngine)
    ├─ SemanticEngine 2  (e.g. LLMEngine)
    └─ ...
    │
    ▼
AIDoc (with block.semantic populated)
```

---

## Components

### `SemanticProcessor`

The orchestrator. It runs engines sequentially and enforces structural integrity after every call. Users do not invoke engines directly — the processor manages all execution.

```python
from aidoc_sdk.semantic.processor import SemanticProcessor

processor = SemanticProcessor(engines=[rule_engine, llm_engine])
doc = processor.process(doc)
```

**Constructor parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `engines` | `List[SemanticEngine]` | required | Ordered list of engine instances |
| `fail_fast` | `bool` | `True` | `True` = raise on engine error; `False` = log and continue |

---

### `SemanticEngine`

Abstract base class. Every engine must declare `name`, `version`, and implement `process()`:

```python
from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.semantic.decorators import engine
from aidoc_sdk.core.models import AIDoc

@engine("my_engine")
class MyEngine(SemanticEngine):
    name = "my_engine"
    version = "1.0"

    def process(self, document: AIDoc) -> AIDoc:
        # Enrich block.semantic — must return NEW AIDoc instance
        return document.model_copy(deep=True)

    async def process_async(self, document: AIDoc) -> AIDoc:
        return self.process(document)
```

**Contract:**
- **MUST** return a new `AIDoc` instance — never mutate in place.
- **MAY** modify `block.semantic` fields.
- **MUST NOT** modify `block.id`, `block.text`, `block.rows`, sections, `spec`, or `source_hash`.

---

### `RuleEngine`

Built-in **deterministic expert** engine. Applies pattern matching (regex) to extract structured semantics (Requirements, Prohibitions, Definitions, Conditions, References) from paragraph text with total precision.

```python
from aidoc_sdk.semantic.rule_engine import RuleEngine
```

---

### `LLMEngine`

Built-in **independent reasoning** engine. Acts as an autonomous semantic classifier. It interprets the "meaning" of a document and maps it to the 8 standardized semantic categories, even in the absence of explicit keywords.

```python
from aidoc_sdk.semantic.llm.engine import LLMEngine
```

---

## Metadata

After each engine runs, `SemanticProcessor` appends a `SemanticLayerInfo` record to `doc.meta.processor.semantic_layers`:

```json
{
  "name": "rule_engine",
  "version": "1.0",
  "status": "success",
  "error": null
}
```

On failure (in `fail_fast=False` mode):

```json
{
  "name": "llm_engine",
  "version": "1.0",
  "status": "failed",
  "error": "ConnectTimeout: API unreachable"
}
```

This provides a full, per-engine audit trail embedded directly in the document.

---

## Enabling Semantic Processing

Via `PipelineConfig`:

```python
from aidoc_sdk import process_file
from aidoc_sdk.pipeline.config import PipelineConfig

config = PipelineConfig(
    enable_semantic=True,
    semantic_engines=["rule_engine", "llm_engine"],
    semantic_fail_fast=False   # Resilient mode — log failures and continue
)

doc = process_file("contract.pdf", config=config)

for layer in doc.meta.processor.semantic_layers:
    print(layer.name, layer.status, layer.error)
```

---

## Semantic Object Types

Engines place structured objects into `block.semantic`. The SDK enforces a standardized 8-category taxonomy:

| Category | Type | Key Fields |
|---|---|---|
| **Descriptive** | `statement` | `content`, `confidence` (LLM only) |
| | `definition` | `term`, `meaning` |
| | `reference` | `target`, `ref_type` (`internal` \| `external`) |
| **Normative** | `requirement` | `subject`, `action`, `modality`, `object` (opt) |
| | `prohibition` | `subject`, `action`, `modality` |
| **Procedural** | `instruction` | `action`, `target` |
| **Conditional** | `condition` | `trigger`, `effect` |
| | `exception` | `provision`, `exemption` |

> **Note**: In the Python SDK, the `exception` type is implemented as the `LogicException` model to avoid namespace collisions with built-in Python exceptions.

See [aidoc-spec/spec.md](../aidoc-spec/spec.md) for the full specification.
