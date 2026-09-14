"""
AIDoc SDK — End-to-End Example
================================

Demonstrates three levels of document processing:

    1. Basic structural parsing          → sample_parsed_base.json
    2. Rule-based semantic enrichment    → sample_parsed_rule_engine.json
    3. LLM-based semantic enrichment     → sample_parsed_llm.json

For the LLM example a mock client is used to simulate a real provider
(e.g. OpenAI, Anthropic). Swap `MockLLMClient` with your own implementation
of `BaseLLMClient` to connect to a real model.
"""

import asyncio
from pathlib import Path

from aidoc_sdk import process_file
from aidoc_sdk.core.serializer import to_canonical_json
from aidoc_sdk.pipeline import Pipeline
from aidoc_sdk.pipeline.config import PipelineConfig, ExecutionMode
from aidoc_sdk.pipeline.context import PipelineContext
from aidoc_sdk.semantic.llm.client import BaseLLMClient
from aidoc_sdk.semantic.llm.engine import LLMEngine
from aidoc_sdk.semantic.registry import register_engine


# ─────────────────────────────────────────────────────────────────────────────
# Real-World Reference (Commented Out)
# ─────────────────────────────────────────────────────────────────────────────
#
# To use a real LLM, you would implement the BaseLLMClient like this:
#
# import json
# import httpx
#
# class OpenAIClient(BaseLLMClient):
#     name = "openai"
#
#     def __init__(self, api_key: str):
#         self.api_key = api_key
#         self.url = "https://api.openai.com/v1/chat/completions"
#
#     async def generate(self, prompt: str) -> dict:
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }
#         payload = {
#             "model": "gpt-4-turbo-preview",
#             "messages": [{"role": "user", "content": prompt}],
#             "response_format": {"type": "json_object"}
#         }
#         async with httpx.AsyncClient() as client:
#             response = await client.post(self.url, headers=headers, json=payload)
#             response.raise_for_status()
#             return response.json()
#
# # usage:
# # engine = LLMEngine(client=OpenAIClient(api_key="your-key-here"))


# ─────────────────────────────────────────────────────────────────────────────
# Mock LLM Client
# ─────────────────────────────────────────────────────────────────────────────

class MockLLMClient(BaseLLMClient):
    """
    A mock LLM client that returns hard-coded refined semantic JSON
    demonstrating the full 8-category taxonomy.
    """
    name = "mock_llm"

    async def generate(self, prompt: str) -> dict:
        # Simulations of the 8 categorized types:
        # Descriptive (3), Normative (2), Procedural (1), Conditional (2)
        return {
            "items": [
                {
                    "type": "statement",
                    "content": "This document describes the rules for handling confidential information within the organization.",
                    "confidence": 1.0
                },
                {
                    "type": "definition",
                    "term": "Confidential Information",
                    "meaning": "any non-public data, including customer records, financial data, and internal business plans.",
                    "confidence": 0.99
                },
                {
                    "type": "requirement",
                    "subject": "Employees",
                    "action": "must protect all Confidential Information from unauthorized disclosure",
                    "modality": "mandatory",
                    "confidence": 0.98
                },
                {
                    "type": "prohibition",
                    "subject": "Employees",
                    "action": "must not share Confidential Information with external parties without proper authorization",
                    "modality": "mandatory",
                    "confidence": 0.99
                },
                {
                    "type": "instruction",
                    "action": "open the company portal and log in using your assigned credentials",
                    "target": "company portal",
                    "confidence": 0.94
                },
                {
                    "type": "condition",
                    "trigger": "If an employee suspects that Confidential Information has been exposed",
                    "effect": "the employee must report the incident immediately",
                    "confidence": 0.92
                },
                {
                    "type": "exception",
                    "provision": "Employees may not transmit Confidential Information via personal email",
                    "exemption": "authorized by the compliance department",
                    "confidence": 0.95
                },
                {
                    "type": "reference",
                    "target": "Section 12 of the Information Security Handbook",
                    "ref_type": "internal",
                    "confidence": 0.9
                }
            ]
        }


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def save_and_print(document, base_dir: Path, title: str, filename: str) -> None:
    separator = "-" * 60
    print(f"\n{separator}")
    print(f"  {title}")
    print(separator)
    print(f"  Source Hash : {document.meta.source_hash}")
    print(f"  Extractor   : {document.meta.processor.extractor.name} "
          f"v{document.meta.processor.extractor.version}")

    layers = document.meta.processor.semantic_layers
    if layers:
        print("  Semantic Layers:")
        for layer in layers:
            print(f"    • {layer.name} (v{layer.version})  status={layer.status}")
    else:
        print("  Semantic Layers: none")

    canonical_json = to_canonical_json(document)

    output_path = base_dir / filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(canonical_json)

    print(f"\n  Saved -> {filename}")
    print(f"\n{canonical_json}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    base_dir = Path(__file__).parent
    sample_path = base_dir / "sample.txt"

    if not sample_path.exists():
        sample_path.write_text(
            "This Agreement is between the Provider and the User.\n"
            "A 'Breach' means any violation of these terms.\n"
            "The Provider shall deliver monthly reports (see Section 4).\n"
            "The User shall not redistribute the data.\n"
            "If a Breach occurs, then this Agreement may be terminated.\n"
            "To terminate, click the 'Terminate' button.",
            encoding="utf-8"
        )

    print(f"\nProcessing: {sample_path.name}\n")

    # ── 1. Base: structural parsing only ─────────────────────────────────────
    doc_base = process_file(sample_path, config=PipelineConfig(enable_semantic=False))
    save_and_print(
        doc_base, base_dir,
        "OUTPUT 1 — Basic Structural Parsing (no enrichment)",
        "sample_parsed_base.json",
    )

    # ── 2. Rule engine: deterministic regex-based enrichment ─────────────────
    doc_rule = process_file(
        sample_path,
        config=PipelineConfig(enable_semantic=True, semantic_engines=["rule_engine"]),
    )
    save_and_print(
        doc_rule, base_dir,
        "OUTPUT 2 — Rule-Based Semantic Enrichment",
        "sample_parsed_rule_engine.json",
    )

    # ── 3. LLM engine: AI-powered semantic enrichment ────────────────────────
    #
    # The LLMEngine is async-only (it calls an external network API).
    # We register a subclass that injects our chosen client, then run
    # the pipeline through the async execution path.
    #
    class MockLLMEngine(LLMEngine):
        """Concrete engine wired to MockLLMClient. Replace client to use a real LLM."""
        name = "mock_llm_engine"
        version = "1.0"
        def __init__(self) -> None:
            super().__init__(
                client=MockLLMClient(),
                # Optionally supply your own system prompt:
                # custom_system_prompt="Extract only obligations and conditions."
            )

    register_engine(MockLLMEngine)

    config_llm = PipelineConfig(
        execution_mode=ExecutionMode.async_mode,
        enable_semantic=True,
        semantic_engines=["mock_llm_engine"],
    )
    pipeline = Pipeline(config=config_llm)
    context = PipelineContext(config=config_llm, input_path=sample_path)
    doc_llm = asyncio.run(pipeline.execute_context_async(context))

    save_and_print(
        doc_llm, base_dir,
        "OUTPUT 3 — LLM-Powered Semantic Enrichment (mock client)",
        "sample_parsed_llm.json",
    )


if __name__ == "__main__":
    main()
