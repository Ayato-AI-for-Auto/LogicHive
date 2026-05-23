import time
import uuid
from collections.abc import Callable
from functools import wraps

from core.logging_config import current_run_id, get_logger

logger = get_logger(__name__)


def trace_execution(func: Callable):
    """
    Decorator to track function execution boundaries, latency, and inputs/outputs.
    Integrates with Loguru via 'extra' fields and contextvars.
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Generate a run_id if not present
        is_new_trace = False
        if current_run_id.get() == "system":
            current_run_id.set(str(uuid.uuid4()))
            is_new_trace = True

        run_id = current_run_id.get()
        func_name = func.__name__
        start_time = time.perf_counter()

        # Log Boundary START
        logger.info(
            f"START: {func_name}",
            function_name=func_name,
            run_id=run_id,
            inputs={"args": str(args), "kwargs": str(kwargs)},
            trace_type="EXECUTION_BOUNDARY",
            is_new_trace=is_new_trace,
        )

        try:
            result = await func(*args, **kwargs)
            latency = time.perf_counter() - start_time

            # Log Boundary SUCCESS
            logger.info(
                f"SUCCESS: {func_name}",
                function_name=func_name,
                run_id=run_id,
                latency_sec=latency,
                output=str(result)[:500],  # Truncate large outputs in logs
                trace_type="EXECUTION_BOUNDARY",
                is_new_trace=is_new_trace,
            )
            return result
        except Exception as e:
            latency = time.perf_counter() - start_time
            logger.error(
                f"ERROR: {func_name} - {str(e)}",
                function_name=func_name,
                run_id=run_id,
                latency_sec=latency,
                error=str(e),
                traceback=True,
                trace_type="EXECUTION_BOUNDARY",
                is_new_trace=is_new_trace,
            )
            raise
        finally:
            if is_new_trace:
                current_run_id.set("system")

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Sync version of the tracer
        is_new_trace = False
        if current_run_id.get() == "system":
            current_run_id.set(str(uuid.uuid4()))
            is_new_trace = True

        run_id = current_run_id.get()
        func_name = func.__name__
        start_time = time.perf_counter()

        logger.info(
            f"START: {func_name} (sync)",
            function_name=func_name,
            run_id=run_id,
            inputs={"args": str(args), "kwargs": str(kwargs)},
            trace_type="EXECUTION_BOUNDARY",
        )

        try:
            result = func(*args, **kwargs)
            latency = time.perf_counter() - start_time
            logger.info(
                f"SUCCESS: {func_name}",
                function_name=func_name,
                run_id=run_id,
                latency_sec=latency,
                trace_type="EXECUTION_BOUNDARY",
            )
            return result
        except Exception as e:
            latency = time.perf_counter() - start_time
            logger.error(
                f"ERROR: {func_name} - {str(e)}",
                function_name=func_name,
                run_id=run_id,
                latency_sec=latency,
                error=str(e),
                trace_type="EXECUTION_BOUNDARY",
            )
            raise
        finally:
            if is_new_trace:
                current_run_id.set("system")

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
