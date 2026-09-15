from aidoc_sdk.pipeline import Pipeline, PipelineConfig
from aidoc_sdk.extraction.registry import get_extractor
from aidoc_sdk.core.hashing import hash_bytes
from aidoc_sdk.core.serializer import to_canonical_json


def main():

    config = PipelineConfig(
        enable_semantic=True,
        semantic_engines=["rule_engine"]
    )
    pipeline = Pipeline(config=config)

    extractor = get_extractor("txt")

    text = "This must be done.\nIf X then Y."
    data = text.encode("utf-8")

    raw_document = extractor.extract_from_bytes(data)

    source_hash = hash_bytes(data)

    doc = pipeline.run(
        raw_document=raw_document,
        source_hash=source_hash,
        extractor_name=extractor.name,
        extractor_version=extractor.version,
    )

    print(to_canonical_json(doc))


if __name__ == "__main__":
    main()
