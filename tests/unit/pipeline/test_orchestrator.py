import pytest
import asyncio

from aidoc_sdk.pipeline.orchestrator import PipelineOrchestrator
from aidoc_sdk.pipeline.stages import PipelineStage
from aidoc_sdk.pipeline.context import PipelineContext
from aidoc_sdk.pipeline.config import PipelineConfig
from aidoc_sdk.exceptions import StageExecutionError


# ---------------------------------------------------------------------------
# Dummy Stages for Testing
# ---------------------------------------------------------------------------

class DummyStage(PipelineStage):
    name = "dummy"

    def execute(self, context):
        return context.replace(artifacts={"ran": True})


class FailingStage(PipelineStage):
    name = "fail"

    def execute(self, context):
        raise RuntimeError("boom")


class AsyncDummyStage(PipelineStage):
    name = "async_dummy"

    async def execute_async(self, context):
        return context.replace(artifacts={"async_ran": True})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_orchestrator_runs_stages():
    context = PipelineContext(config=PipelineConfig())

    orchestrator = PipelineOrchestrator([DummyStage()])
    result = orchestrator.run(context)

    assert result.artifacts["ran"] is True


def test_orchestrator_wraps_stage_failure():
    context = PipelineContext(config=PipelineConfig())

    orchestrator = PipelineOrchestrator([FailingStage()])

    with pytest.raises(StageExecutionError):
        orchestrator.run(context)


def test_orchestrator_async_execution():
    context = PipelineContext(config=PipelineConfig())

    orchestrator = PipelineOrchestrator([AsyncDummyStage()])

    result = asyncio.run(orchestrator.run_async(context))

    assert result.artifacts["async_ran"] is True
