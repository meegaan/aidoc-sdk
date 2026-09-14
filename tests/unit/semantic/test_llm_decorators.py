"""
Tests for semantic/llm/decorators.py

Covers:
- retry_on_failure: succeeds on first try (async)
- retry_on_failure: succeeds after N retries (async)
- retry_on_failure: raises EngineExecutionError after max retries (async)
- retry_on_failure: preserves function name
- handle_provider_errors: passes through on success (async)
- handle_provider_errors: wraps unknown exceptions into SemanticError (async)
- handle_provider_errors: passes through SemanticError unchanged
- handle_provider_errors: passes through EngineExecutionError unchanged
- log_execution: returns result without interference (async)
- log_execution: propagates exceptions (async)
"""

import asyncio
import pytest

from aidoc_sdk.exceptions import EngineExecutionError, SemanticError
from aidoc_sdk.semantic.llm.decorators import (
    retry_on_failure,
    handle_provider_errors,
    log_execution,
)


# ---------------------------------------------------------------------------
# retry_on_failure (async)
# ---------------------------------------------------------------------------

class TestRetryOnFailure:

    def test_succeeds_on_first_try(self):
        call_count = 0

        @retry_on_failure(retries=3, delay=0)
        async def good_fn():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = asyncio.run(good_fn())
        assert result == "ok"
        assert call_count == 1

    def test_succeeds_after_retries(self):
        call_count = 0

        @retry_on_failure(retries=3, delay=0)
        async def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("transient error")
            return "recovered"

        result = asyncio.run(flaky_fn())
        assert result == "recovered"
        assert call_count == 3

    def test_raises_engine_execution_error_after_max_retries(self):
        @retry_on_failure(retries=2, delay=0)
        async def always_fails():
            raise RuntimeError("permanent error")

        with pytest.raises(EngineExecutionError):
            asyncio.run(always_fails())

    def test_preserves_function_name(self):
        @retry_on_failure(retries=1, delay=0)
        async def my_function():
            return "x"

        assert my_function.__name__ == "my_function"


# ---------------------------------------------------------------------------
# handle_provider_errors (async)
# ---------------------------------------------------------------------------

class TestHandleProviderErrors:

    def test_passes_through_on_success(self):
        @handle_provider_errors
        async def good():
            return 42

        result = asyncio.run(good())
        assert result == 42

    def test_wraps_unknown_exception_into_semantic_error(self):
        @handle_provider_errors
        async def bad():
            raise ConnectionError("network failure")

        with pytest.raises(SemanticError):
            asyncio.run(bad())

    def test_passes_through_semantic_error_unchanged(self):
        @handle_provider_errors
        async def already_semantic():
            raise SemanticError("already typed error")

        with pytest.raises(SemanticError, match="already typed error"):
            asyncio.run(already_semantic())

    def test_passes_through_engine_execution_error_unchanged(self):
        @handle_provider_errors
        async def engine_error():
            raise EngineExecutionError("engine error")

        with pytest.raises(EngineExecutionError):
            asyncio.run(engine_error())


# ---------------------------------------------------------------------------
# log_execution (async)
# ---------------------------------------------------------------------------

class TestLogExecution:

    def test_log_execution_does_not_suppress_return_value(self):
        @log_execution
        async def fn():
            return {"key": "value"}

        result = asyncio.run(fn())
        assert result == {"key": "value"}

    def test_log_execution_propagates_exceptions(self):
        @log_execution
        async def bad():
            raise ValueError("oops")

        with pytest.raises(ValueError, match="oops"):
            asyncio.run(bad())

