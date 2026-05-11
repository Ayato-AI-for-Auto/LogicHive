import os
import sys
from contextvars import ContextVar

from loguru import logger

# Context variable for tracing request/execution flows
current_run_id: ContextVar[str] = ContextVar("run_id", default="system")


def get_logger(name: str):
    """Returns a configured logger with run_id propagation."""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Configure Loguru (if not already configured)
    # Note: We use a sink that outputs JSONL for traceability
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[name]}:{function}:{line}</cyan> - [RunID: <yellow>{extra[run_id]}</yellow>] - <level>{message}</level>",
        level="INFO",
        enqueue=True,
    )
    logger.add(
        "logs/logichive.jsonl",
        format="{message}",
        serialize=True,  # This makes it JSON
        level="DEBUG",
        rotation="10 MB",
        retention="1 week",
    )

    # Return a logger with the name injected into extra
    return logger.bind(name=name).patch(
        lambda record: record["extra"].update(run_id=current_run_id.get())
    )
