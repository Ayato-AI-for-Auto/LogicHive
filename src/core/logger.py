import sys
from pathlib import Path

from loguru import logger

# Log directory setup
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Define file paths
LOG_FILE = LOG_DIR / "logichive.jsonl"
ERROR_FILE = LOG_DIR / "error.log"

# Remove default handler
logger.remove()

# 1. Add JSON formatted log for general events
# Rotation: 2 files kept (logichive.jsonl + logichive.1.jsonl)
logger.add(
    LOG_FILE,
    format="{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | {level} | {message} | {extra}",
    serialize=True,
    rotation="2",
    retention="2",
    level="DEBUG",
)

# 2. Add Error-isolated log (non-JSON for readability, or JSON if preferred)
# Keeping JSON for consistency with the requirement
logger.add(
    ERROR_FILE,
    format="{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | {level} | {message} | {extra}",
    serialize=True,
    level="ERROR",
    rotation="2",
    retention="2",
)

# Add stdout for development visibility
logger.add(sys.stderr, level="INFO")

def get_logger(name: str):
    return logger.bind(name=name)
