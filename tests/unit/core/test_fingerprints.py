from aidoc_sdk.core.fingerprints import (
    structural_fingerprint,
    full_document_fingerprint,
)


def test_structural_fingerprint_stable(canonical_document):
    assert structural_fingerprint(canonical_document) == \
           structural_fingerprint(canonical_document)


def test_full_fingerprint_stable(canonical_document):
    assert full_document_fingerprint(canonical_document) == \
           full_document_fingerprint(canonical_document)
