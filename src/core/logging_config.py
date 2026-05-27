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
        "name": record["extra"]["name"],
        "function": record["function"],
        "line": record["line"],
        "run_id": record["extra"].get("run_id", "system"),
    }
    if exception:
        subset["exception"] = {
            "type": str(exception.type.__name__),
            "value": str(exception.value),
            "traceback": str(exception)
        }
    return json.dumps(subset)

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Simplified generation management using loguru's built-in rotation
    # 'retention=2' ensures only 2 files are kept.
    logger.remove()

    # 1. Console Sink (Human Readable)
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[name]}</cyan> - {message}",
        level="DEBUG",
    )

    # 2. Main JSON Sink
    logger.add(
        os.path.join(log_dir, "logichive.jsonl"),
        format="{extra[serialized]}",
        level="DEBUG",
        rotation="10 MB",
        retention=2,
        enqueue=True,
    )

    # 3. Isolated Error Sink
    logger.add(
        os.path.join(log_dir, "error.log"),
        format="{extra[serialized]}",
        level="ERROR",
        rotation="10 MB",
        retention=2,
        enqueue=True,
    )

    def patcher(record):
        # Ensure 'name' is in extra so the console formatter doesn't raise a KeyError
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
