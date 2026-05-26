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
        "name": record["extra"].get("name", "unknown"),
        "function": record["function"],
        "line": record["line"],
        "run_id": record["extra"].get("run_id", "system"),
    }
    if exception:
        subset["exception"] = {
            "type": exception.type.__name__,
            "value": str(exception.value),
            "traceback": str(exception)
        }
    return json.dumps(subset)

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    latest_log = os.path.join(log_dir, "logichive.jsonl")
    previous_log = os.path.join(log_dir, "logichive_previous.jsonl")

    # Strictly keep 2 generations
    if os.path.exists(latest_log):
        try:
            if os.path.exists(previous_log):
                os.remove(previous_log)
            os.rename(latest_log, previous_log)
        except PermissionError:
            # On Windows, logs can be locked by other processes (like active pytest workers)
            # We skip rotation rather than crashing.
            pass

    logger.remove()

    # 1. Console Sink (Human Readable)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[name]}:{function}:{line}</cyan> - [RunID: <yellow>{extra[run_id]}</yellow>] - <level>{message}</level>",
        level="INFO",
    )

    # 2. Main JSON Sink
    logger.add(latest_log, format="{extra[serialized]}", level="DEBUG", enqueue=True)

    # 3. Isolated Error Sink
    logger.add(
        os.path.join(log_dir, "error.log"),
        format="{extra[serialized]}",
        level="ERROR",
        enqueue=True,
    )

    def patcher(record):
        record["extra"]["run_id"] = current_run_id.get()
        record["extra"]["name"] = record["extra"].get("name", record["name"])
        record["extra"]["serialized"] = json_serializer(record)

    logger.configure(patcher=patcher)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

def get_logger(name: str):
    return logger.bind(name=name)

setup_logging()
