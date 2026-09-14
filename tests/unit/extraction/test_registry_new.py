import pytest
from pathlib import Path

from aidoc_sdk.extraction.registry import ExtractorRegistry
from aidoc_sdk.extraction.base import BaseExtractor
from aidoc_sdk.exceptions import ConfigurationError

class DummyJSONExtractor(BaseExtractor):
    name = "dummy_json"
    version = "1.0"
    supported_extensions = (".json",)

    def extract(self, path: Path):
        return None

def test_registry_registration_and_lookup():
    reg = ExtractorRegistry()
    reg.register(DummyJSONExtractor)

    # By explicit name
    ext1 = reg.get_by_format("dummy_json")
    assert isinstance(ext1, DummyJSONExtractor)

    # By file extension Auto-detect
    ext2 = reg.get_by_extension(".json")
    assert isinstance(ext2, DummyJSONExtractor)

    # By for_file Path
    ext3 = reg.for_file(Path("/fake/path/document.json"))
    assert isinstance(ext3, DummyJSONExtractor)

def test_registry_unsupported():
    reg = ExtractorRegistry()
    
    with pytest.raises(ConfigurationError):
        reg.for_file("test.unknown")
