import json
import logging
import os
import sys
from contextvars import ContextVar

from loguru import logger

# Context variable for tracing request/execution flows
current_run_id: ContextVar[str] = ContextVar("run_id", default="system")


class InterceptHandler(logging.Handler):
    """
    Default handler from Loguru documentation for intercepting standard library logging messages.
    See: https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def json_serializer(record):
    """Custom JSON serializer to ensure consistent structure."""
    exception = None
    if record["exception"] is not None:
        type_name, value, tb = record["exception"]
        exception = {
            "type": type_name.__name__ if hasattr(type_name, "__name__") else str(type_name),
            "value": str(value),
            "traceback": record["extra"].get("traceback_str") or ""  # Loguru usually handles tb formatting
        }
    
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "name": record["extra"].get("name", "unknown"),
        "function": record["function"],
        "line": record["line"],
        "run_id": record["extra"].get("run_id", "system"),
    }
    if exception:
        subset["exception"] = exception
    return json.dumps(subset)


def setup_logging():
    """Initializes and configures Loguru with custom rotation and error isolation."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 1. Custom Rotation: Keep only the last 2 execution logs
    latest_log = os.path.join(log_dir, "logichive.jsonl")
    previous_log = os.path.join(log_dir, "logichive_previous.jsonl")

    if os.environ.get("PYTEST_CURRENT_TEST") is None:
        try:
            if os.path.exists(latest_log):
                if os.path.exists(previous_log):
                    os.remove(previous_log)
                os.rename(latest_log, previous_log)
        except (PermissionError, FileNotFoundError):
            pass

    logger.remove()  # Remove default handler

    # 2. Console Sink (Human Readable)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[name]}:{function}:{line}</cyan> - [RunID: <yellow>{extra[run_id]}</yellow>] - <level>{message}</level>",
        level="INFO",
        enqueue=True,
    )

    # 3. Main Structured Log Sink (JSON)
    logger.add(
        latest_log,
        format="{extra[serialized]}",
        level="DEBUG",
        enqueue=True,
    )

    # 4. Isolated Error Sink (JSON)
    logger.add(
        os.path.join(log_dir, "error.log"),
        format="{extra[serialized]}",
        level="ERROR",
        enqueue=True,
        rotation="10 MB",
        retention="1 month",
    )

    # 5. Global Patcher for RunID and Serialization
    def patcher(record):
        record["extra"]["run_id"] = current_run_id.get()
        record["extra"]["name"] = record["extra"].get("name", record["name"])
        record["extra"]["serialized"] = json_serializer(record)

    logger.configure(patcher=patcher)

    # 6. Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


def get_logger(name: str):
    """Returns a logger bound with a specific name."""
    return logger.bind(name=name)


# Initialize on module load
setup_logging()

