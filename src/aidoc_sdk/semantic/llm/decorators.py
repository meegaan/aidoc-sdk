"""
LLM Execution Decorators
========================

Provides resiliency and logging wrappers for LLM operations.
Ensures external I/O failures do not crash the pipeline unexpectedly
and maps provider errors to domain exceptions.

All decorators are async-aware — they correctly handle both sync and async
decorated functions by detecting coroutines at decoration time.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from aidoc_sdk.exceptions import EngineExecutionError, SemanticError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry_on_failure(retries: int = 3, delay: float = 1.0) -> Callable[[F], F]:
    """
    Retry an LLM operation upon failure.

    Args:
        retries: Number of allowed retries before giving up.
        delay: Initial delay between retries (in seconds). Backs off exponentially.

    Supports both sync and async decorated functions.
    """
    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                attempt = 0
                current_delay = delay
                while attempt <= retries:
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        attempt += 1
                        if attempt > retries:
                            logger.error(
                                "LLM operation failed after %d retries: %s",
                                retries, str(e), exc_info=True
                            )
                            raise EngineExecutionError(
                                f"LLM call failed after {retries} retries: {str(e)}"
                            ) from e

                        logger.warning(
                            "LLM operation failed (attempt %d/%d). Retrying in %.1fs: %s",
                            attempt, retries, current_delay, str(e)
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= 2  # Exponential backoff
            return cast(F, async_wrapper)
        else:
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                attempt = 0
                current_delay = delay
                while attempt <= retries:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        attempt += 1
                        if attempt > retries:
                            logger.error(
                                "LLM operation failed after %d retries: %s",
                                retries, str(e), exc_info=True
                            )
                            raise EngineExecutionError(
                                f"LLM call failed after {retries} retries: {str(e)}"
                            ) from e

                        logger.warning(
                            "LLM operation failed (attempt %d/%d). Retrying in %.1fs: %s",
                            attempt, retries, current_delay, str(e)
                        )
                        time.sleep(current_delay)
                        current_delay *= 2
            return cast(F, sync_wrapper)
    return decorator


def handle_provider_errors(func: F) -> F:
    """
    Standardize generic or provider-specific exceptions into aidoc_sdk exceptions.

    Supports both sync and async decorated functions.
    """
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except (EngineExecutionError, SemanticError):
                raise
            except Exception as e:
                raise SemanticError(f"LLM Provider Error: {str(e)}") from e
        return cast(F, async_wrapper)
    else:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except (EngineExecutionError, SemanticError):
                raise
            except Exception as e:
                raise SemanticError(f"LLM Provider Error: {str(e)}") from e
        return cast(F, sync_wrapper)


def log_execution(func: F) -> F:
    """
    Log execution time of an LLM call.

    Supports both sync and async decorated functions.
    """
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.monotonic()
            try:
                logger.debug("Executing LLM operation: %s", func.__name__)
                result = await func(*args, **kwargs)
                duration = time.monotonic() - start_time
                logger.debug("LLM operation '%s' completed in %.2fs", func.__name__, duration)
                return result
            except Exception:
                duration = time.monotonic() - start_time
                logger.error("LLM operation '%s' failed after %.2fs", func.__name__, duration)
                raise
        return cast(F, async_wrapper)
    else:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.monotonic()
            try:
                logger.debug("Executing LLM operation: %s", func.__name__)
                result = func(*args, **kwargs)
                duration = time.monotonic() - start_time
                logger.debug("LLM operation '%s' completed in %.2fs", func.__name__, duration)
                return result
            except Exception:
                duration = time.monotonic() - start_time
                logger.error("LLM operation '%s' failed after %.2fs", func.__name__, duration)
                raise
        return cast(F, sync_wrapper)
