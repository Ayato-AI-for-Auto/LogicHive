import sys
from loguru import logger
from pathlib import Path
import os
from contextvars import ContextVar
import uuid

# Context variable for tracing request/execution flows
current_run_id: ContextVar[str] = ContextVar("current_run_id", default="system")

# Create logs directory if not exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Remove default logger
logger.remove()


# Inject run_id into every log record
def add_run_id(record):
    record["extra"]["run_id"] = current_run_id.get()


# Apply the patcher globally
logger = logger.patch(add_run_id)

# Add JSON logging for production/traceability
log_file = log_dir / "logichive.jsonl"
logger.add(
    log_file,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",  # Format is mostly ignored due to serialize=True
    serialize=True,
    level="DEBUG",  # Capture all intermediate logic for traceability
)

# Add colored logging for development console
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | [RunID: <magenta>{extra[run_id]}</magenta>] - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO"),
)


def get_logger(name):
    return logger.bind(name=name)
