import asyncio
import ctypes
import os

from core.execution.base import (
    ExecutionLogs,
    ExecutionResult,
    ExecutionStatus,
)
from core.logging_config import get_logger

from .base import BaseSandbox

logger = get_logger(__name__)

# Windows Constants
JOBOBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9

# Limit Flags
JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

# Access Rights
PROCESS_SET_QUOTA = 0x0100
PROCESS_TERMINATE = 0x0200



class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("DataOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("DataTransferCount", ctypes.c_ulonglong),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class WindowsNativeSandbox(BaseSandbox):
    """
    Windows-native sandbox using Job Objects to enforce hardware and process boundaries.
    Also features a user-space monitoring fallback for added resiliency.
    """

    def __init__(self):
        self.job_handle = None
        if os.name == "nt":
            self._init_job_object()

    def _init_job_object(self):
        try:
            # Create a new Job Object
            self.job_handle = ctypes.windll.kernel32.CreateJobObjectW(None, None)
            if not self.job_handle:
                logger.error("WindowsSandbox: Failed to create Job Object.")
                return

            logger.info("WindowsSandbox: Successfully initialized Job Object.")
        except Exception as e:
            logger.error(f"WindowsSandbox: Failed to initialize Job Object: {e}", exc_info=True)

    def _configure_limits(self, memory_limit_mb: int):
        if not self.job_handle:
            return

        try:
            # Convert MB to bytes
            mem_limit_bytes = memory_limit_mb * 1024 * 1024

            limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            # Enforce process memory, job memory, limit process creation (prevents fork bomb), and kill children on close
            limits.BasicLimitInformation.LimitFlags = (
                JOB_OBJECT_LIMIT_PROCESS_MEMORY
                | JOB_OBJECT_LIMIT_JOB_MEMORY
                | JOB_OBJECT_LIMIT_ACTIVE_PROCESS
                | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            )
            limits.BasicLimitInformation.ActiveProcessLimit = 10  # Max 10 concurrent processes
            limits.ProcessMemoryLimit = mem_limit_bytes
            limits.JobMemoryLimit = mem_limit_bytes

            res = ctypes.windll.kernel32.SetInformationJobObject(
                self.job_handle,
                JOBOBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
                ctypes.byref(limits),
                ctypes.sizeof(limits),
            )
            if not res:
                err = ctypes.windll.kernel32.GetLastError()
                logger.error(f"WindowsSandbox: Failed to SetInformationJobObject. Error code: {err}")
            else:
                logger.debug(f"WindowsSandbox: Set memory limit to {memory_limit_mb}MB and process limit to 10.")
        except Exception as e:
            logger.error(f"WindowsSandbox: Error configuring limits: {e}", exc_info=True)

    def _kill_process_tree(self, pid: int):
        """Kills a process and all its children cross-platform."""
        import psutil

        try:
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            parent.kill()
            logger.debug(f"WindowsSandbox: Process tree for PID {pid} killed.")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    async def _monitor_resources(self, process, limit_mb, done_event, state):
        import psutil

        try:
            while not done_event.is_set():
                try:
                    parent = psutil.Process(process.pid)
                    if not parent.is_running():
                        break
                    total_mem = parent.memory_info().rss + sum(
                        c.memory_info().rss for c in parent.children(recursive=True)
                    )
                    if (total_mem / 1024 / 1024) > limit_mb:
                        logger.warning(f"WindowsSandbox: Memory limit exceeded in fallback monitor. Killing {process.pid}")
                        state["memory_exceeded"] = True
                        self._kill_process_tree(process.pid)
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                except Exception as e:
                    logger.error(f"WindowsSandbox: Unexpected error in resource monitor: {e}")
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"WindowsSandbox: Fallback resource monitor crashed: {e}")

    async def execute_command(
        self,
        cmd: list[str],
        cwd: str,
        env: dict[str, str] | None = None,
        timeout: float = 10.0,
        memory_limit_mb: int = 256,
        result_file: str | None = None,
    ) -> ExecutionResult:
        if os.name != "nt" or not self.job_handle:
            # Fallback to standard subprocess run on non-Windows/failed initialization
            logger.warning("WindowsSandbox: Falling back to un-isolated subprocess execution.")
            return await self._fallback_execute(cmd, cwd, env, timeout)

        self._configure_limits(memory_limit_mb)

        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Launch process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=process_env,
        )

        # Associate process with Job Object immediately
        h_process = ctypes.windll.kernel32.OpenProcess(
            PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, process.pid
        )
        if h_process:
            assign_res = ctypes.windll.kernel32.AssignProcessToJobObject(
                self.job_handle, h_process
            )
            if not assign_res:
                err = ctypes.windll.kernel32.GetLastError()
                logger.error(f"WindowsSandbox: AssignProcessToJobObject failed with code {err}")
            ctypes.windll.kernel32.CloseHandle(h_process)
        else:
            logger.error("WindowsSandbox: Failed to OpenProcess for assignment to Job Object.")

        # Track state across tasks (User-space fallback monitor)
        state = {"memory_exceeded": False}
        done_event = asyncio.Event()
        monitor_task = asyncio.create_task(
            self._monitor_resources(process, memory_limit_mb, done_event, state)
        )

        # Wait for completion or timeout
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            if state["memory_exceeded"]:
                return ExecutionResult(
                    status=ExecutionStatus.MEMORY_LIMIT,
                    logs=ExecutionLogs(stderr="Memory limit exceeded."),
                )

            # Check if terminated by job memory limits (kernel-level)
            status = ExecutionStatus.SUCCESS if process.returncode == 0 else ExecutionStatus.FAILURE
            if process.returncode in [3221225495, -1073741797, 0xC0000017]:
                status = ExecutionStatus.MEMORY_LIMIT
                stderr = f"Memory limit of {memory_limit_mb}MB exceeded. " + stderr

            return self._build_result(status, stdout, stderr, process.returncode, result_file)

        except asyncio.TimeoutError:
            self._kill_process_tree(process.pid)
            await process.wait()
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                logs=ExecutionLogs(stderr="Execution timed out."),
            )
        finally:
            done_event.set()
            monitor_task.cancel()

    async def _fallback_execute(
        self, cmd: list[str], cwd: str, env: dict[str, str] | None, timeout: float
    ) -> ExecutionResult:
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=process_env,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            status = ExecutionStatus.SUCCESS if process.returncode == 0 else ExecutionStatus.FAILURE
            return self._build_result(status, stdout, stderr, process.returncode)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.wait()
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                logs=ExecutionLogs(stderr="Execution timed out."),
            )

    def _build_result(
        self,
        status: ExecutionStatus,
        stdout: str,
        stderr: str,
        returncode: int,
        result_file: str | None = None,
    ) -> ExecutionResult:
        import json
        from pathlib import Path

        from core.execution.base import ExecutionError, Result

        results = []
        error = None

        if result_file and Path(result_file).exists():
            try:
                raw = json.loads(Path(result_file).read_text(encoding="utf-8"))
                if "main_result" in raw:
                    results.append(
                        Result(data=raw["main_result"], metadata={"is_main_result": True})
                    )
                if raw.get("error"):
                    err_info = raw["error"]
                    error = ExecutionError(
                        name=err_info.get("name", "UnknownError"),
                        value=err_info.get("value", ""),
                        traceback=err_info.get("traceback", ""),
                    )
                    status = ExecutionStatus.FAILURE
            except Exception as e:
                logger.error(f"WindowsSandbox: Failed to parse result file: {e}")

        if status == ExecutionStatus.FAILURE and not error:
            error = ExecutionError(
                name="RuntimeError", value=f"Exit code {returncode}", traceback=stderr
            )

        return ExecutionResult(
            status=status,
            logs=ExecutionLogs(stdout=stdout, stderr=stderr),
            results=results,
            error=error,
        )
