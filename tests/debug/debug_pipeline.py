from aidoc_sdk.pipeline.pipeline import Pipeline, PipelineConfig
from aidoc_sdk.extraction.registry import get_extractor
from aidoc_sdk.core.raw import RawDocument, RawParagraph

def debug():
    config = PipelineConfig(
        enable_semantic=True,
        semantic_engines=["rule_engine"]
    )
    pipeline = Pipeline(config=config)
    
    raw_document = RawDocument(elements=[RawParagraph(order=0, text="This is a test document with must and shall.")])
    source_hash = "a" * 64
    
    try:
        doc = pipeline.run(
            raw_document=raw_document,
            source_hash=source_hash,
            extractor_name="txt",
            extractor_version="1.0"
        )
        print("Success!")
        print(f"Processor: {doc.meta.processor}")
        print(f"Semantic layers: {doc.meta.processor.semantic_layers}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug()
