from aidoc_sdk.semantic.rule_engine import RuleEngine
from aidoc_sdk.core.models import AIDoc, Section, ParagraphBlock, Requirement, Prohibition, Meta
from aidoc_sdk.core.version import SPEC_VERSION

VALID_ID = "0" * 64

def test_rule_engine_requirement_detection(canonical_document):
    # Text with "shall" triggers Requirement
    doc = AIDoc(
        spec=SPEC_VERSION,
        meta=Meta(source_hash=VALID_ID),
        sections=[
            Section(
                id=VALID_ID,
                title="S1",
                level=1,
                blocks=[ParagraphBlock(id=VALID_ID, type="paragraph", text="The user shall click the button.")]
            )
        ]
    )
    engine = RuleEngine()
    enriched = engine.process(doc)
    
    sem = enriched.sections[0].blocks[0].semantic
    assert len(sem) == 1
    assert isinstance(sem[0], Requirement)
    assert sem[0].modality == "mandatory"

def test_rule_engine_prohibition_detection():
    doc = AIDoc(
        spec=SPEC_VERSION,
        meta=Meta(source_hash=VALID_ID),
        sections=[
            Section(
                id=VALID_ID,
                title="S1",
                level=1,
                blocks=[ParagraphBlock(id=VALID_ID, type="paragraph", text="You shall not pass.")]
            )
        ]
    )
    engine = RuleEngine()
    enriched = engine.process(doc)
    
    sem = enriched.sections[0].blocks[0].semantic
    assert len(sem) == 1
    assert isinstance(sem[0], Prohibition)
    assert sem[0].modality == "prohibited"

def test_rule_engine_no_mutation(canonical_document):
    engine = RuleEngine()
    enriched = engine.process(canonical_document)
    assert enriched is not canonical_document
