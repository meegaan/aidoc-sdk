import asyncio
import pytest
from unittest.mock import AsyncMock

from aidoc_sdk.semantic.llm.engine import LLMEngine
from aidoc_sdk.core.models import (
    Statement,
    Requirement,
    Prohibition,
    Condition,
    Definition,
    Instruction,
    Reference,
    LogicException,
    SemanticType,
)

@pytest.fixture
def mock_client():
    client = AsyncMock()
    return client

def test_enrich_refined_types(mock_client, canonical_document):
    # Setup mock response with one of each type
    mock_client.generate.return_value = {
        "items": [
            {"type": "statement", "content": "Info", "confidence": 0.9},
            {"type": "requirement", "subject": "A", "action": "B", "modality": "mandatory", "confidence": 0.9},
            {"type": "prohibition", "subject": "C", "action": "D", "modality": "mandatory", "confidence": 0.9},
            {"type": "definition", "term": "T", "meaning": "M", "confidence": 0.9},
            {"type": "instruction", "action": "Do", "target": "It", "confidence": 0.9},
            {"type": "reference", "target": "S1", "ref_type": "internal", "confidence": 0.9},
            {"type": "condition", "trigger": "X", "effect": "Y", "confidence": 0.9},
            {"type": "exception", "provision": "P1", "exemption": "E1", "confidence": 0.9},
        ]
    }

    engine = LLMEngine(client=mock_client)
    
    async def run_test():
        return await engine.process_async(canonical_document)

    enriched_doc = asyncio.run(run_test())

    # Check the first paragraph block
    semantics = enriched_doc.sections[0].blocks[0].semantic
    assert len(semantics) == 8
    
    # Check a few specific ones
    types = [type(s) for s in semantics]
    assert Statement in types
    assert Requirement in types
    assert Prohibition in types
    assert LogicException in types
    assert Condition in types

def test_prohibition_mapping(mock_client, canonical_document):
    mock_client.generate.return_value = {
        "items": [
            {
                "type": "prohibition",
                "subject": "User",
                "action": "shall not share",
                "modality": "mandatory",
                "confidence": 0.99
            }
        ]
    }
    
    engine = LLMEngine(client=mock_client)
    
    async def run_test():
        return await engine.process_async(canonical_document)

    enriched_doc = asyncio.run(run_test())
    
    proh = enriched_doc.sections[0].blocks[0].semantic[0]
    assert isinstance(proh, Prohibition)
    assert proh.type == SemanticType.prohibition
    assert proh.subject == "User"
    assert "shall not share" in proh.action
