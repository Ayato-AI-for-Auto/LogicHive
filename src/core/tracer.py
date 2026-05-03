import inspect
import time
import uuid
from functools import wraps
from typing import Any, Callable

from core.logging_config import current_run_id, get_logger

logger = get_logger(__name__)


def trace_execution(func: Callable) -> Callable:
    """
    Decorator to add comprehensive traceability to functions.
    - Generates or propagates a unique run_id using ContextVars.
    - Logs inputs (args, kwargs) upon entry.
    - Measures end-to-end execution latency (wall time via perf_counter).
    - Logs outputs upon successful completion.
    - Logs exceptions and latency upon failure.
    """

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Propagate or create run_id
            run_id = current_run_id.get()
            is_new_trace = False
            token = None

            if run_id == "system" or not run_id:
                run_id = str(uuid.uuid4())
                token = current_run_id.set(run_id)
                is_new_trace = True

            # Use bind to attach specific context to these log records (beyond what patcher does)
            bound_logger = logger.bind(
                function_name=func.__name__,
                trace_type="EXECUTION_BOUNDARY",
                is_new_trace=is_new_trace,
            )

            # Limit input logging size to avoid flooding for huge code strings
            safe_args = [
                str(a)[:500] + "..." if isinstance(a, str) and len(a) > 500 else a for a in args
            ]
            safe_kwargs = {
                k: (str(v)[:500] + "..." if isinstance(v, str) and len(v) > 500 else v)
                for k, v in kwargs.items()
            }

            bound_logger.info(
                f"START: {func.__name__}",
                inputs={"args": repr(safe_args), "kwargs": repr(safe_kwargs)},
            )

            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                latency = time.perf_counter() - start_time

                safe_result = (
                    str(result)[:1000] + "..."
                    if isinstance(result, str) and len(result) > 1000
                    else result
                )

                bound_logger.info(
                    f"SUCCESS: {func.__name__}",
                    latency_sec=latency,
                    output=repr(safe_result),
                )
                return result
            except Exception as e:
                latency = time.perf_counter() - start_time
                bound_logger.exception(
                    f"ERROR: {func.__name__} failed",
                    latency_sec=latency,
                    error=str(e),
                )
                raise
            finally:
                if token:
                    current_run_id.reset(token)

        return async_wrapper

    else:

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Propagate or create run_id
            run_id = current_run_id.get()
            is_new_trace = False
            token = None

            if run_id == "system" or not run_id:
                run_id = str(uuid.uuid4())
                token = current_run_id.set(run_id)
                is_new_trace = True

            bound_logger = logger.bind(
                function_name=func.__name__,
                trace_type="EXECUTION_BOUNDARY",
                is_new_trace=is_new_trace,
            )

            safe_args = [
                str(a)[:500] + "..." if isinstance(a, str) and len(a) > 500 else a for a in args
            ]
            safe_kwargs = {
                k: (str(v)[:500] + "..." if isinstance(v, str) and len(v) > 500 else v)
                for k, v in kwargs.items()
            }

            bound_logger.info(
                f"START: {func.__name__}",
                inputs={"args": repr(safe_args), "kwargs": repr(safe_kwargs)},
            )

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                latency = time.perf_counter() - start_time

                safe_result = (
                    str(result)[:1000] + "..."
                    if isinstance(result, str) and len(result) > 1000
                    else result
                )

                bound_logger.info(
                    f"SUCCESS: {func.__name__}",
                    latency_sec=latency,
                    output=repr(safe_result),
                )
                return result
            except Exception as e:
                latency = time.perf_counter() - start_time
                bound_logger.exception(
                    f"ERROR: {func.__name__} failed",
                    latency_sec=latency,
                    error=str(e),
                )
                raise
            finally:
                if token:
                    current_run_id.reset(token)

        return sync_wrapper
