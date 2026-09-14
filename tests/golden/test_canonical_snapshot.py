import json
from aidoc_sdk.core.serializer import to_canonical_json


def test_canonical_snapshot(canonical_document):
    expected_raw = open("tests/golden/canonical_simple.json").read()
    expected = json.loads(expected_raw)

    actual = json.loads(to_canonical_json(canonical_document))

    assert actual == expected

# def test_canonical_snapshot(canonical_document):
#     from aidoc_sdk.core.serializer import to_canonical_json
#     print(to_canonical_json(canonical_document))
#     assert False
