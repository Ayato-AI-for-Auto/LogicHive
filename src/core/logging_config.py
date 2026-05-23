import os
import sys
from contextvars import ContextVar

from loguru import logger

# Context variable for tracing request/execution flows
current_run_id: ContextVar[str] = ContextVar("run_id", default="system")

def setup_logging():
    """Initializes and configures Loguru with custom rotation and error isolation."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 1. Custom Rotation: Keep only the last 2 execution logs
    # We rotate by moving current 'latest.log' to 'previous.log' on startup
    latest_log = os.path.join(log_dir, "logichive.jsonl")
    previous_log = os.path.join(log_dir, "logichive_previous.jsonl")

    if os.path.exists(latest_log):
        if os.path.exists(previous_log):
            os.remove(previous_log)
        os.rename(latest_log, previous_log)

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
        format="{message}",
        serialize=True,
        level="DEBUG",
        enqueue=True,
    )

    # 4. Isolated Error Sink (JSON)
    # Only stores ERROR and higher, kept persistently
    logger.add(
        os.path.join(log_dir, "error.log"),
        format="{message}",
        serialize=True,
        level="ERROR",
        enqueue=True,
        rotation="10 MB",
        retention="1 month",
    )

# Initialize on module load
setup_logging()

def get_logger(name: str):
    """Returns a configured logger with run_id propagation."""
    return logger.bind(name=name).patch(
        lambda record: record["extra"].update(run_id=current_run_id.get())
    )
