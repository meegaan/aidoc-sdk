# Structural Guardrails

## Purpose

Semantic engines enrich documents with meaning, but they must **never alter document structure**. The guardrail system enforces this contract automatically for every engine call.

---

## The Rule

| Semantic engines **MAY** modify | Semantic engines **MUST NOT** modify |
|---|---|
| `block.semantic` | `block.id` |
| | `block.text` |
| | `block.rows` (tables) |
| | `section.id`, `section.title`, `section.level` |
| | `sections` order or count |
| | `doc.spec` |
| | `doc.meta.source_hash` |

---

## How It Works

The `SemanticProcessor` enforces guardrails **after every engine call** using three checks:

```
before = structural_fingerprint(doc)
enriched = engine.process(doc)

assert_same_spec(doc, enriched)           # spec version unchanged
assert_same_source_hash(doc, enriched)    # source hash unchanged
assert_structure_unchanged(doc, enriched) # structural fingerprint unchanged
```

If any assertion fails, the violation is wrapped as an `EngineExecutionError`.

---

## Structural Fingerprint

`structural_fingerprint(doc: AIDoc) -> str` computes a **SHA-256 hash** of the structure-only view of the document.

**Included in fingerprint:**
- `doc.spec`
- `doc.meta.source_hash`
- Every `section.id`, `section.title`, `section.level`
- Every `block.id`, `block.type`, `block.text`
- Every `block.rows` (for tables)

**Excluded from fingerprint:**
- `block.semantic` — enrichment output, may change freely
- `meta.processor` — operational metadata, must not affect structure

This means a valid engine that only modifies `block.semantic` will produce an identical fingerprint before and after, and it will pass all guardrail checks.

---

## Detection Example

**Before engine call:**
```json
{ "id": "abc123...", "text": "Supplier shall deliver.", "semantic": [] }
```
Fingerprint: `2d4f3b...`

**After a malicious engine modifies text:**
```json
{ "id": "abc123...", "text": "The supplier must deliver goods.", "semantic": [] }
```
Fingerprint: `9c1e7a...`

**Result:** `2d4f3b... != 9c1e7a...` → `EngineExecutionError` raised immediately.

---

## Error Types

| Error | Meaning |
|---|---|
| `StructuralViolationError` | Fingerprint mismatch or spec/hash mutation detected |
| `EngineExecutionError` | Wraps both structural violations and engine runtime errors |

---

## Implementation Files

| File | Role |
|---|---|
| `src/aidoc_sdk/core/fingerprints.py` | `structural_fingerprint()` and `_build_structural_view()` |
| `src/aidoc_sdk/core/guardrails.py` | `assert_structure_unchanged()`, `assert_same_spec()`, `assert_same_source_hash()` |
| `src/aidoc_sdk/semantic/processor.py` | Calls guardrails after every engine execution |

---

## Fail-Fast vs. Continue Mode

By default, any guardrail failure immediately raises `EngineExecutionError` and halts the pipeline.

In `semantic_fail_fast=False` mode, **only runtime engine errors** are caught and logged — guardrail violations (structural mutations) always raise immediately, regardless of `fail_fast`, because they represent a programming contract violation, not a transient failure.
