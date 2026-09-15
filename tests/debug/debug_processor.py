from aidoc_sdk.core.models import AIDoc, Meta, Section, ParagraphBlock, ProcessorInfo, ExtractorInfo
from aidoc_sdk.core.version import SPEC_VERSION, CORE_CONTRACT_VERSION
from aidoc_sdk.semantic.processor import SemanticProcessor
from aidoc_sdk.semantic.rule_engine import RuleEngine

def test_node():
    processor = ProcessorInfo(
        aidoc_core=CORE_CONTRACT_VERSION,
        extractor=ExtractorInfo(name="test", version="1.0"),
        semantic_layers=[]
    )
    
    meta = Meta(source_hash="a" * 64, processor=processor)
    
    doc = AIDoc(
        spec=SPEC_VERSION,
        meta=meta,
        sections=[
            Section(
                id="b" * 64,
                title="Document",
                level=1,
                blocks=[
                    ParagraphBlock(id="c" * 64, type="paragraph", text="Must do this.")
                ]
            )
        ]
    )
    
    engine = RuleEngine()
    processor_instance = SemanticProcessor([engine])
    
    try:
        enriched = processor_instance.process(doc)
        print("SemanticProcessor Success!")
        print(f"Processor exists: {enriched.meta.processor is not None}")
        print(f"Layer count: {len(enriched.meta.processor.semantic_layers)}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_node()
