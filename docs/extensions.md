# Extending AIDoc SDK

## Overview

The SDK is designed for extension at two points:

1. **Extraction** — Add support for new file formats.
2. **Semantic Engines** — Add domain-specific AI enrichment logic.

Both extension points use the same pattern: a decorator that registers the component, plus optional entry-point discovery for packaged plugins.

---

## 1. Custom Extractors

### Inline Registration

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
        # Read the file and build a RawDocument
        ...
```

After this decorator runs (i.e. after importing your module), the SDK will automatically resolve `.xml` files to `XMLExtractor`.

### Plugin Package (Entry Points)

To distribute an extractor as a package that does not require explicit imports:

**`pyproject.toml`:**
```toml
[project.entry-points."aidoc_sdk.extractors"]
xml = "my_package.extractor:XMLExtractor"
```

The `ExtractorRegistry` calls `importlib.metadata.entry_points(group="aidoc_sdk.extractors")` on first use and loads all registered plugins automatically.

### Collision Protection

If two extractors claim the same extension, `ExtractorConflictError` is raised immediately at registration time:

```
ExtractorConflictError: Extension '.pdf' is already registered by 'pdf'.
Cannot register 'my_pdf'.
```

---

## 2. Custom Semantic Engines

### Inline Registration

```python
from aidoc_sdk.semantic.base import SemanticEngine
from aidoc_sdk.semantic.decorators import engine
from aidoc_sdk.core.models import AIDoc

@engine("my_engine")
class MyEngine(SemanticEngine):
    name = "my_engine"
    version = "1.0"

    def process(self, document: AIDoc) -> AIDoc:
        # Enrich block.semantic — return a NEW AIDoc, never mutate
        updated_sections = ...
        return document.model_copy(update={"sections": updated_sections})

    async def process_async(self, document: AIDoc) -> AIDoc:
        # Override for native async (e.g. LLM API calls)
        return self.process(document)
```

Activate via `PipelineConfig`:

```python
from aidoc_sdk import process_file
from aidoc_sdk.pipeline.config import PipelineConfig

doc = process_file("contract.pdf", config=PipelineConfig(
    enable_semantic=True,
    semantic_engines=["my_engine"]
))
```

### Plugin Package (Entry Points)

For a distributable domain engine package (e.g. `aidoc-sdk-legal`):

**`pyproject.toml`:**
```toml
[project.entry-points."aidoc_sdk.engines"]
legal = "aidoc_legal.engine:LegalEngine"
```

> **Note:** Built-in engine entry-point discovery uses the `aidoc_sdk.engines` group. Ensure your entry-point group matches the registry's configured group.

### Engine Contract Checklist

Before publishing an engine, verify:

- [ ] `name` class attribute matches the `@engine` decorator argument
- [ ] `version` class attribute is declared (raises `TypeError` at import if missing)
- [ ] `process()` returns a **new** `AIDoc` — never mutates the input
- [ ] Only `block.semantic` is modified — no `block.id`, `block.text`, or structural changes
- [ ] `process_async()` is implemented for async pipelines (can delegate to `process()`)

---

## 3. Registry Internals

Both registries (extraction and semantic) follow the same patterns:

| Feature | Extraction | Semantic |
|---|---|---|
| Decorator | `@extractor("name")` | `@engine("name")` |
| Registry module | `aidoc_sdk.extraction.registry` | `aidoc_sdk.semantic.registry` |
| Entry-point group | `aidoc_sdk.extractors` | `aidoc_sdk.engines` |
| Thread safety | `threading.Lock` | (registry is read-only after startup) |
| Lazy loading | Yes — built-ins loaded on first use | Manual import triggers registration |

---

## 4. Testing Your Extension

```python
from aidoc_sdk import process_file
from aidoc_sdk.pipeline.config import PipelineConfig
from aidoc_sdk.core.fingerprints import structural_fingerprint

# Import your module to trigger registration
import my_package.extractor  # or engine

# Test extractor
doc = process_file("sample.xml")
assert doc.meta.source_hash  # extraction succeeded

# Test engine
config = PipelineConfig(enable_semantic=True, semantic_engines=["my_engine"])
doc_enriched = process_file("sample.txt", config=config)
fp_before = structural_fingerprint(doc)
fp_after  = structural_fingerprint(doc_enriched)
assert fp_before == fp_after  # structure unchanged — guardrails passed
```
