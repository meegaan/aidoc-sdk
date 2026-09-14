# Determinism in AIDoc SDK

## Core Principle

The AIDoc SDK is split into two clearly defined processing categories:

| Category | Layers | Guarantee |
|---|---|---|
| **Deterministic** | Extraction, Canonicalization, Metadata | Identical input → identical output, always |
| **Non-Deterministic** | Semantic (LLM engines) | Output may vary between calls |

---

## Deterministic Processing

Every layer up to and including `MetadataStage` is strictly deterministic.

**What this means in practice:**

```python
doc1 = process_file("contract.pdf")
doc2 = process_file("contract.pdf")

assert doc1.meta.source_hash == doc2.meta.source_hash  # ✓ always equal
assert structural_fingerprint(doc1) == structural_fingerprint(doc2)  # ✓ always equal
```

**How it is guaranteed:**

- Block and section IDs are SHA-256 hashes derived exclusively from their canonical content.
- Canonicalization applies deterministic UTF-8 normalization and whitespace rules.
- Serialization uses strict canonical JSON: sorted keys, no whitespace, no floating-point ambiguity.
- No timestamp, random seed, or runtime entropy enters the structural layers.

---

## Non-Deterministic Processing

LLM-based semantic engines (e.g. `LLMEngine`) can produce different `block.semantic` values across identical calls — model temperature, API versioning, and context windowing can all influence results.

**What this means:**

```python
doc1 = process_file("contract.pdf", config=PipelineConfig(
    enable_semantic=True, semantic_engines=["llm_engine"]
))
doc2 = process_file("contract.pdf", config=PipelineConfig(
    enable_semantic=True, semantic_engines=["llm_engine"]
))

# Structural fingerprints still match
assert structural_fingerprint(doc1) == structural_fingerprint(doc2)  # ✓

# But semantic content may differ
# doc1.sections[0].blocks[0].semantic != doc2.sections[0].blocks[0].semantic  (possible)
```

**Critical guarantee:** Non-determinism is **strictly confined to `block.semantic`**. The structural fingerprint and all canonical fields remain deterministic even when LLM engines are active.

---

## Engine Audit Trail

Every engine run — whether deterministic or not — is recorded in `doc.meta.processor.semantic_layers`:

```json
[
  { "name": "rule_engine", "version": "1.0", "status": "success", "error": null },
  { "name": "llm_engine",  "version": "1.0", "status": "success", "error": null }
]
```

This provides:
- **Reproducibility:** Know exactly which engines produced which document.
- **Auditability:** Identify when and why an engine failed.
- **Versioning:** Engine `version` field allows diff tracking across deployments.

---

## Why This Split Matters

| Use case | Suitable layer |
|---|---|
| Content-addressable storage / deduplication | Core (deterministic) — use `source_hash` |
| Document integrity verification | Core (deterministic) — use `structural_fingerprint()` |
| Legal / audit trail | Core + semantic_layers audit log |
| AI-powered entity extraction | Semantic (`LLMEngine` — probabilistic) |
| Reproducible semantic pipelines | Semantic (`RuleEngine` — deterministic) |
| Production LLM enrichment | Use `semantic_fail_fast=False` for resilience |

---

## `structural_fingerprint` vs `full_document_fingerprint`

The SDK exposes two fingerprint functions:

```python
from aidoc_sdk import structural_fingerprint, full_document_fingerprint

# Stable across enrichment — excludes block.semantic and processor metadata
fp1 = structural_fingerprint(doc)

# Full document hash — changes if any semantic content changes
fp2 = full_document_fingerprint(doc)
```

Use `structural_fingerprint` for integrity checks across enrichment runs.
Use `full_document_fingerprint` when you need to detect any change at all.
