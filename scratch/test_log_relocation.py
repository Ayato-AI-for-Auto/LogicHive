from core.logging_config import get_logger
import os

logger = get_logger("test")
logger.info("Testing log relocation")

home_dir = os.path.expanduser("~/.logichive")
log_file = os.path.join(home_dir, "logs", "logichive.jsonl")

if os.path.exists(log_file):
    print(f"SUCCESS: Log file found at {log_file}")
else:
    print(f"FAILURE: Log file NOT found at {log_file}")
    # List actual log dir for debugging
    log_dir = os.path.expanduser("~/.logichive/logs")
    if os.path.exists(log_dir):
        print(f"Log directory exists: {log_dir}")
        print(f"Contents: {os.listdir(log_dir)}")
    else:
        print(f"Log directory does NOT exist: {log_dir}")
