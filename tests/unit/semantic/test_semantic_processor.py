from aidoc_sdk.semantic.processor import SemanticProcessor
from aidoc_sdk.semantic.rule_engine import RuleEngine
from aidoc_sdk.core.models import ProcessorInfo, ExtractorInfo
from aidoc_sdk.core.version import CORE_CONTRACT_VERSION


def test_semantic_processor_preserves_structure(canonical_document):
    # SemanticProcessor requires ProcessorInfo to already exist (injected by MetadataStage)
    processor = ProcessorInfo(
        aidoc_core=CORE_CONTRACT_VERSION,
        extractor=ExtractorInfo(name="test", version="1.0"),
        semantic_layers=[]
    )
    doc = canonical_document.model_copy(
        update={"meta": canonical_document.meta.model_copy(update={"processor": processor})}
    )

    processor_instance = SemanticProcessor([RuleEngine()])
    enriched = processor_instance.process(doc)

    assert enriched.spec == doc.spec
