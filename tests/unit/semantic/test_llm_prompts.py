"""
Tests for semantic/llm/prompts.py

Covers:
- build_prompt uses default system prompt when no custom given
- build_prompt uses custom prompt when provided
- Prompt always contains the target text
"""

from aidoc_sdk.semantic.llm.prompts import build_prompt, DEFAULT_SYSTEM_PROMPT


def test_build_prompt_uses_default_system_prompt():
    prompt = build_prompt("Some text")
    assert DEFAULT_SYSTEM_PROMPT in prompt
    assert "Some text" in prompt


def test_build_prompt_uses_custom_system_prompt():
    custom = "You are a specialist. Extract obligations only."
    prompt = build_prompt("Target text", custom_prompt=custom)
    assert custom in prompt
    assert DEFAULT_SYSTEM_PROMPT not in prompt
    assert "Target text" in prompt


def test_build_prompt_none_custom_uses_default():
    prompt = build_prompt("Hello world", custom_prompt=None)
    assert DEFAULT_SYSTEM_PROMPT in prompt


def test_build_prompt_contains_separator():
    prompt = build_prompt("Some text")
    assert "--- TEXT TO ANALYZE ---" in prompt
    assert "--- END TEXT ---" in prompt


def test_build_prompt_with_empty_text():
    prompt = build_prompt("")
    assert DEFAULT_SYSTEM_PROMPT in prompt
