from aidoc_sdk.pipeline.pipeline import Pipeline, PipelineConfig
from aidoc_sdk.pipeline.context import PipelineContext
from aidoc_sdk.pipeline.stages import CanonicalStage, MetadataStage
from aidoc_sdk.core.raw import RawDocument, RawParagraph

def debug_metadata():
    raw_document = RawDocument(elements=[RawParagraph(order=0, text="Test")])
    source_hash = "a" * 64
    
    context = PipelineContext(
        config=PipelineConfig(),
        raw_document=raw_document,
        artifacts={"source_hash": source_hash}
    )
    
    cs = CanonicalStage()
    context = cs.execute(context)
    print(f"After Canonical: processor={context.canonical_document.meta.processor}")
    
    ms = MetadataStage("test_ext", "1.0")
    context = ms.execute(context)
    print(f"After Metadata: processor={context.canonical_document.meta.processor}")
    if context.canonical_document.meta.processor:
        print(f"Semantic layers: {context.canonical_document.meta.processor.semantic_layers}")

if __name__ == "__main__":
    debug_metadata()
