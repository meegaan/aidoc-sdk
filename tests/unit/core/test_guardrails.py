import pytest

from aidoc_sdk.core.guardrails import assert_structure_unchanged
from aidoc_sdk.exceptions import StructuralViolationError
from aidoc_sdk.core.models import Section, ParagraphBlock


def test_guardrail_detects_structure_change(canonical_document):
    original = canonical_document

    # Rebuild first block with changed text (legal model copy)
    first_section = original.sections[0]
    first_block = first_section.blocks[0]

    modified_block = ParagraphBlock(
        id=first_block.id,
        type="paragraph",
        text="Modified text",
        semantic=first_block.semantic,
    )

    modified_section = Section(
        id=first_section.id,
        title=first_section.title,
        level=first_section.level,
        blocks=[modified_block] + list(first_section.blocks[1:]),
    )

    modified_doc = original.model_copy(
        update={"sections": [modified_section] + list(original.sections[1:])}
    )

    with pytest.raises(StructuralViolationError):
        assert_structure_unchanged(original, modified_doc)
