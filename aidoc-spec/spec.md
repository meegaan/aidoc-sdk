aidoc-sdk Specification (v1.0)

---

1. Overview

aidoc-sdk is a language-independent document format designed for immutable,
deterministic, and semantically enriched structured documents.

The specification defines the canonical structure and processing rules
for aidoc-sdk documents independent of any programming language
implementation.

An implementation of aidoc-sdk MUST follow the rules defined in this
document and validate documents against the official aidoc-sdk JSON Schema.

---

2. Core Principles

2.1 Immutability

aidoc-sdk documents are immutable. Any modification to the structure or
content of a document MUST produce a new document with new identifiers.

2.2 Determinism

For a given input and the same aidoc-sdk core version, implementations MUST
produce identical structural output and identifiers.

2.3 Structural Fingerprinting

Sections and blocks are identified using SHA-256 hashes derived from
their canonical structural representation.

2.4 Semantic Enrichment

Semantic information MAY be attached to blocks without modifying the
structural identity of the document.

Semantic enrichment MUST NOT affect section or block identifiers.

---

3. Document Structure

An aidoc-sdk document consists of the following top-level fields.

{
"spec": "aidoc@1.0",
"meta": { ... },
"sections": [ ... ]
}

Fields

spec
The specification version identifier.

meta
Operational metadata describing the origin and processing context.

sections
An ordered array of document sections forming the canonical structure.

---

4. Metadata

meta
source_hash
created_at (optional)
processor (optional)

source_hash
SHA-256 hash of the original input bytes used to create the document.

created_at
Optional ISO-8601 timestamp representing when the document was generated.

processor
Metadata describing the software that generated or processed the document.

ProcessorInfo
    aidoc_core        Version string of the processing core.
    extractor         Object with name and version fields.
    semantic_layers   Ordered array of SemanticLayerInfo records.

SemanticLayerInfo (one record per semantic engine invocation)
    name      Engine name identifier.
    version   Engine version string.
    status    Execution result. MUST be "success" or "failed".
    error     Optional error message. Present only when status is "failed".
              MUST be null or absent on success.

Implementations MUST preserve semantic_layers order.
Implementations MUST NOT modify semantic_layers outside the semantic stage.

---


5. Sections

Sections provide hierarchical organization for document content.

Section
id
title
level
blocks

id
A deterministic SHA-256 identifier derived from canonical section
content.

title
Human-readable section title.

level
Hierarchy level where 1 represents the top-level section.

blocks
Ordered list of content blocks within the section.

---

6. Blocks

Blocks are the atomic structural units of an aidoc-sdk document.

Every block MUST contain the following fields:

id
type
semantic

id
Deterministic SHA-256 identifier.

type
Block type identifier.

semantic
Array containing semantic enrichment objects.

---

7. Paragraph Block

Represents normalized textual content.

{
"type": "paragraph",
"text": "content"
}

text
Normalized UTF-8 textual content.

---

8. Table Block

Represents structured tabular data.

{
"type": "table",
"rows": [["a","b"],["c","d"]]
}

rows
Two-dimensional array representing table rows.

Tables MUST be rectangular. All rows MUST contain the same number of
columns.

---

9. Semantic Enrichment

Semantic objects provide machine-readable meaning attached to blocks.

Supported semantic object types:

--- DESCRIPTIVE ---

statement
General informational text, assertions, or background context.

definition
Defines a specific term, concept, or technical acronym.

reference
Links to internal or external targets (Section X, Clause Y).

--- NORMATIVE ---

requirement
Positive obligations or mandatory rules (shall, must).

prohibition
Negative obligations or forbidden actions (shall not, must not).

--- PROCEDURAL ---

instruction
Actionable steps, procedures, or directions to follow.

--- CONDITIONAL ---

condition
Prerequisites or dependencies that trigger other rules (If... then...).

exception
Overrides, exemptions, or "unless" clauses that negate other rules.

Semantic objects MUST NOT influence block or section identifiers.

---

10. Canonicalization Rules

To ensure determinism, implementations MUST follow canonical JSON rules.

1. JSON object keys MUST be sorted.
2. Insignificant whitespace MUST be removed.
3. Strings MUST be UTF-8 encoded.
4. Hexadecimal hashes MUST be lowercase.
5. Multi-line strings MUST follow consistent newline normalization.

---

11. Block Identifier Algorithm

Block identifiers MUST be generated using the following algorithm.

1. Serialize block content excluding the "id" field.
2. Serialize using canonical JSON formatting.
3. Encode the serialized content using UTF-8.
4. Apply SHA-256 hashing.
5. Encode the result as lowercase hexadecimal.

---

12. Compliance

An implementation is considered compliant if:

1. Documents validate against the official aidoc-sdk JSON Schema.
2. Identical inputs produce identical structural identifiers.
3. The original source hash is preserved.
4. Semantic enrichment does not alter structural identifiers.

---

13. Versioning

aidoc-sdk specification versions follow semantic versioning.

Examples

aidoc@1.0
aidoc@1.1
aidoc@2.0

Versioning Rules

Minor versions MAY introduce optional fields or non-breaking extensions.

Major versions MAY modify canonicalization rules, identifier algorithms,
or structural constraints.
