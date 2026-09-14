from aidoc_sdk.core.normalizer import normalize_text


def test_normalization_deterministic():
    text = "Hello   World\r\n\r\n"
    result = normalize_text(text)
    assert result == "Hello World"
