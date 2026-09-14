from aidoc_sdk.core.serializer import to_canonical_json


import json

def test_json_is_sorted(canonical_document):
    data = json.loads(to_canonical_json(canonical_document))
    assert list(data.keys()) == sorted(data.keys())
