"""
LLM Prompt Templates and Construction
=====================================

Provides structured prompt generation for the LLMEngine.
Ensures the LLM receives deterministic instructions to output JSON
that strictly matches the required schemas.
"""

from typing import Optional

DEFAULT_SYSTEM_PROMPT = """
You are an expert legal and technical document analyst. 
Your task is to extract semantic meaning from the provided text block.

You MUST return a JSON object with an \"items\" list. Categorize your extraction into these 8 types:

--- DESCRIPTIVE (The \"What\") ---
1. \"statement\": General informational text, assertions, or background context.
2. \"definition\": Defines a specific term, concept, or technical acronym.
3. \"reference\": Pointers to other sections, external laws, or documents.

--- NORMATIVE (The \"Must/Must Not\") ---
4. \"requirement\": Positive obligations or mandatory rules (e.g., \"shall\", \"must\").
5. \"prohibition\": Negative obligations or forbidden actions (e.g., \"shall not\", \"must not\").

--- PROCEDURAL (The \"How\") ---
6. \"instruction\": Actionable steps, procedures, or directions to follow.

--- CONDITIONAL (The \"If/Unless\") ---
7. \"condition\": Prerequisites or dependencies that trigger other rules.
8. \"exception\": Overrides, exemptions, or \"unless\" clauses that negate other rules.

JSON Schema for items:
- statement: {\"type\": \"statement\", \"content\": \"...\", \"confidence\": 0.0-1.0}
- definition: {\"type\": \"definition\", \"term\": \"...\", \"meaning\": \"...\", \"confidence\": 0.0-1.0}
- reference: {\"type\": \"reference\", \"target\": \"...\", \"ref_type\": \"internal|external\", \"confidence\": 0.0-1.0}
- requirement: {\"type\": \"requirement\", \"subject\": \"...\", \"action\": \"...\", \"object\": \"...\", \"modality\": \"mandatory|optional\", \"confidence\": 0.0-1.0}
- prohibition: {\"type\": \"prohibition\", \"subject\": \"...\", \"action\": \"...\", \"object\": \"...\", \"modality\": \"mandatory|optional\", \"confidence\": 0.0-1.0}
- instruction: {\"type\": \"instruction\", \"action\": \"...\", \"target\": \"...\", \"confidence\": 0.0-1.0}
- condition: {\"type\": \"condition\", \"trigger\": \"...\", \"effect\": \"...\", \"confidence\": 0.0-1.0}
- exception: {\"type\": \"exception\", \"provision\": \"...\", \"exemption\": \"...\", \"confidence\": 0.0-1.0}

Return ONLY valid JSON. If no semantic meaning is found, return {\"items\": []}.
"""


def build_prompt(text: str, custom_prompt: Optional[str] = None) -> str:
    """
    Construct the final prompt to be sent to the LLM.

    Args:
        text: The block of text to analyze.
        custom_prompt: Optional override for the system instructions.

    Returns:
        The combined instructional prompt and target text.
    """
    instruction = custom_prompt if custom_prompt is not None else DEFAULT_SYSTEM_PROMPT
    
    return f"{instruction}\n\n--- TEXT TO ANALYZE ---\n{text}\n--- END TEXT ---"
