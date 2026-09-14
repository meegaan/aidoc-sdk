from aidoc_sdk.core.canonical import canonicalize


def test_canonical_builds_sections(simple_raw_document, simple_source_hash):
    doc = canonicalize(simple_raw_document, simple_source_hash)

    assert len(doc.sections) >= 1
    assert doc.meta.source_hash == simple_source_hash
    assert doc.spec.startswith("aidoc@")
