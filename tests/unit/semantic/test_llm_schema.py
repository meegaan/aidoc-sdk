import pytest
from pydantic import ValidationError

from aidoc_sdk.semantic.llm.schema import (
    LLMResponse,
    LLMStatement,
    LLMDefinition,
    LLMReference,
    LLMRequirement,
    LLMProhibition,
    LLMInstruction,
    LLMCondition,
    LLMLogicException,
)

# ---------------------------------------------------------------------------
# DESCRIPTIVE
# ---------------------------------------------------------------------------

def test_statement_validation():
    item = LLMStatement(type="statement", content="This is a test", confidence=0.8)
    assert item.type == "statement"
    assert item.content == "This is a test"
    assert item.confidence == 0.8

def test_definition_validation():
    item = LLMDefinition(type="definition", term="AI", meaning="Artificial Intelligence", confidence=0.99)
    assert item.type == "definition"
    assert item.term == "AI"
    assert item.meaning == "Artificial Intelligence"

def test_reference_validation():
    item = LLMReference(type="reference", target="Section 1", ref_type="internal", confidence=0.7)
    assert item.type == "reference"
    assert item.target == "Section 1"
    assert item.ref_type == "internal"

# ---------------------------------------------------------------------------
# NORMATIVE
# ---------------------------------------------------------------------------

def test_requirement_validation():
    item = LLMRequirement(
        type="requirement", 
        subject="Party A", 
        action="deliver", 
        modality="mandatory", 
        confidence=0.95
    )
    assert item.type == "requirement"
    assert item.subject == "Party A"

def test_prohibition_validation():
    item = LLMProhibition(
        type="prohibition", 
        subject="Party B", 
        action="divulge", 
        modality="mandatory", 
        confidence=0.99
    )
    assert item.type == "prohibition"
    assert item.action == "divulge"

# ---------------------------------------------------------------------------
# PROCEDURAL
# ---------------------------------------------------------------------------

def test_instruction_validation():
    item = LLMInstruction(type="instruction", action="Click OK", target="Button", confidence=0.7)
    assert item.type == "instruction"
    assert item.action == "Click OK"

# ---------------------------------------------------------------------------
# CONDITIONAL
# ---------------------------------------------------------------------------

def test_condition_validation():
    item = LLMCondition(type="condition", trigger="If breach", effect="Default", confidence=0.8)
    assert item.type == "condition"
    assert item.trigger == "If breach"

def test_logic_exception_validation():
    item = LLMLogicException(type="exception", provision="Section 1", exemption="Unless X", confidence=0.9)
    assert item.type == "exception"
    assert item.provision == "Section 1"
    assert item.exemption == "Unless X"

# ---------------------------------------------------------------------------
# SHARED CONSTRAINTS
# ---------------------------------------------------------------------------

def test_confidence_bounds():
    with pytest.raises(ValidationError):
        LLMRequirement(type="requirement", subject="X", action="Y", modality="mandatory", confidence=-0.1)
    with pytest.raises(ValidationError):
        LLMRequirement(type="requirement", subject="X", action="Y", modality="mandatory", confidence=1.5)

def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        LLMRequirement(type="requirement", subject="X", action="Y", modality="mandatory", confidence=0.5, extra="bad")

def test_whitespace_stripping():
    item = LLMRequirement(type="requirement", subject="  Party A  ", action="deliver", modality="mandatory", confidence=0.5)
    assert item.subject == "Party A"

def test_response_validation():
    payload = {
        "items": [
            {"type": "statement", "content": "Hello", "confidence": 0.9},
            {"type": "requirement", "subject": "A", "action": "B", "modality": "mandatory", "confidence": 0.8}
        ]
    }
    response = LLMResponse.model_validate(payload)
    assert len(response.items) == 2
    assert isinstance(response.items[0], LLMStatement)
    assert isinstance(response.items[1], LLMRequirement)
