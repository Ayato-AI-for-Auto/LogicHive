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
        # Prevent re-entrant logging from standard library logging internals
        if record.name == "logging" or record.name.startswith("logging."):
            return
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        if not frame:
            logger.opt(exception=record.exc_info).log(level, record.getMessage())
        else:
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
            "traceback": str(exception.traceback),
        }
    return json.dumps(subset)


def rotate_previous_execution_log(filepath):
    """
    Retains exactly the last 2 execution logs.
    Workflow:
    1. If {name}.1.log exists, delete it.
    2. If {name}.log exists, rename it to {name}.1.log.
    3. New execution starts writing to {name}.log.
    """
    if os.path.exists(filepath):
        base, ext = os.path.splitext(filepath)
        backup_path = f"{base}.1{ext}"
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except OSError:
                pass
        try:
            os.rename(filepath, backup_path)
        except OSError:
            pass


def setup_logging():
    # Use user's home directory for logs to avoid permission issues in Program Files
    # and to centralize logs for different execution methods.
    log_dir = os.path.expanduser("~/.logichive/logs")
    os.makedirs(log_dir, exist_ok=True)

    logger.remove()

    # Determine process name to separate logs (settings_ui.py vs mcp_server.py)
    main_script = os.path.basename(sys.argv[0]).lower()
    if "settings" in main_script:
        proc_name = "settings"
    elif "hub" in main_script or "mcp_server" in main_script:
        proc_name = "hub"
    else:
        proc_name = "app"

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

    # File paths
    main_log_path = os.path.join(log_dir, f"{proc_name}.jsonl")
    # Isolated Error Log (As requested: 'error.log' per process for safety)
    error_log_path = os.path.join(log_dir, f"{proc_name}_error.log")

    # Rotate main log for this process
    rotate_previous_execution_log(main_log_path)
    # Rotate error log for this process
    rotate_previous_execution_log(error_log_path)

    # 2. Main JSON Sink (All logs for traceability)
    logger.add(
        main_log_path,
        format="{extra[serialized]}",
        level="DEBUG",
        enqueue=True,
    )

    # 3. Isolated Error Sink (Only ERROR and CRITICAL)
    # Always append to 'error.log' for this execution
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
    for lib in ["faiss", "swig", "httpx", "uvicorn", "httpcore", "urllib3"]:
        logging.getLogger(lib).setLevel(logging.WARNING)


def get_logger(name: str):
    return logger.bind(name=name)


# Initialize on import
setup_logging()
