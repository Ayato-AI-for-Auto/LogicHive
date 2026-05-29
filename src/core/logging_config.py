import json
import logging
import os
import sys
from contextvars import ContextVar

from loguru import logger

# Context variable for tracing request/execution flows
current_run_id: ContextVar[str] = ContextVar("run_id", default="system")

class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def json_serializer(record):
    exception = record["exception"]

    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "name": record["extra"].get("name", record["name"]),
        "function": record["function"],
        "line": record["line"],
        "run_id": record["extra"].get("run_id", "system"),
    }
    if exception:
        subset["exception"] = {
            "type": str(exception.type.__name__),
            "value": str(exception.value),
            "traceback": str(exception.traceback)
        }
    return json.dumps(subset)

def rotate_previous_execution_log(filepath):
    """Keep only the last 2 executions by renaming the current file to _prev."""
    if os.path.exists(filepath):
        base, ext = os.path.splitext(filepath)
        prev_path = f"{base}_prev{ext}"
        if os.path.exists(prev_path):
            try:
                os.remove(prev_path)
            except OSError:
                pass
        try:
            os.rename(filepath, prev_path)
        except OSError:
            pass

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logger.remove()

    # 1. Console Sink (Human Readable)
    if sys.stderr is not None:
        log_format = (
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{extra[name]}</cyan> - {message}"
        )
        logger.add(
            sys.stderr,
            format=log_format,
            level="INFO",
        )

    # Manual rotation for keeping exact last 2 executions
    main_log_path = os.path.join(log_dir, "logichive.jsonl")
    error_log_path = os.path.join(log_dir, "error.log")

    rotate_previous_execution_log(main_log_path)
    rotate_previous_execution_log(error_log_path)

    # 2. Main JSON Sink
    logger.add(
        main_log_path,
        format="{extra[serialized]}",
        level="DEBUG",
        enqueue=True,
    )

    # 3. Isolated Error Sink
    logger.add(
        error_log_path,
        format="{extra[serialized]}",
        level="ERROR",
        enqueue=True,
    )

    def patcher(record):
        record["extra"]["name"] = record["extra"].get("name", record["name"])
        record["extra"]["run_id"] = current_run_id.get()
        record["extra"]["serialized"] = json_serializer(record)

    logger.configure(patcher=patcher)

    # Bridge standard logging to loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # --- NOISE REDUCTION ---
    for lib in ["faiss", "swig", "httpx", "uvicorn"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

def get_logger(name: str):
    return logger.bind(name=name)

# Initialize on import
setup_logging()

