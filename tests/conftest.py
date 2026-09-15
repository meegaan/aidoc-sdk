import pytest

from aidoc_sdk.core.raw import RawDocument, RawParagraph
from aidoc_sdk.core.canonical import canonicalize
from aidoc_sdk.core.hashing import hash_bytes


@pytest.fixture
def simple_raw_document():
    return RawDocument(
        elements=[
            RawParagraph(order=0, text="This must be done."),
            RawParagraph(order=1, text="If X then Y."),
        ]
    )


@pytest.fixture
def simple_source_hash():
    return hash_bytes(b"This must be done.\nIf X then Y.")


@pytest.fixture
def canonical_document(simple_raw_document, simple_source_hash):
    return canonicalize(simple_raw_document, simple_source_hash)
