from aidoc_sdk.pipeline import Pipeline, PipelineConfig


def test_pipeline_runs(simple_raw_document, simple_source_hash):
    config = PipelineConfig(
        enable_semantic=True,
        semantic_engines=["rule_engine"],
    )

    pipeline = Pipeline(config=config)

    result = pipeline.run(
        raw_document=simple_raw_document,
        source_hash=simple_source_hash,
        extractor_name="txt",
        extractor_version="1.0",
    )

    assert result.meta.processor is not None
