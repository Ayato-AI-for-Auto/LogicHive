import asyncio
import json
import os
import tempfile
import time
import traceback
from pathlib import Path

from core.config import ENABLE_ENV_POOLING
from core.logging_config import get_logger

from .base import (
    BaseExecutor,
    ExecutionError,
    ExecutionLogs,
    ExecutionResult,
    ExecutionStatus,
    Result,
)
from .factory import ExecutorFactory

logger = get_logger(__name__)


class EphemeralPythonExecutor(BaseExecutor):
    """
    Executes Python code in an ephemeral environment using `uv`.
    Focuses on security through isolation and rich E2B-compatible telemetry.
    """

    def __init__(self):
        self.name = "python"

    def _kill_process_tree(self, pid: int):
        """Kills a process and all its children cross-platform."""
        import psutil

        try:
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.trace(
                        f"Executor: Child process {child.pid} already gone while killing process tree."
                    )
            parent.kill()
            logger.debug(f"Executor: Process tree for PID {pid} killed.")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            logger.trace(f"Executor: Parent process {pid} already gone while killing process tree.")

    async def execute(
        self,
        code: str,
        test_code: str = "",
        dependencies: list[str] | None = None,
        timeout: int = 20,
        memory_limit_mb: int = 256,
        **kwargs,
    ) -> ExecutionResult:
        logger.info(
            f"Executor: Starting execution [timeout={timeout}s, memory={memory_limit_mb}MB]"
        )
        start_time = time.perf_counter()
        dependencies = dependencies or []
        mock_imports = kwargs.get("mock_imports", [])

        # 1. Acquire Pre-warmed Environment
        pooled_env = await self._acquire_pooled_env(dependencies)

        # 2. Prepare Workspace and Execute
        try:
            with tempfile.TemporaryDirectory(prefix="logichive_exec_") as tmpdir:
                workspace = self._prepare_workspace(tmpdir, code, test_code, mock_imports)
                cmd = self._build_command(pooled_env, workspace["harness_file"], dependencies)

                exec_res = await self._run_subprocess(
                    cmd, tmpdir, timeout, memory_limit_mb, workspace["result_file"]
                )

                duration = time.perf_counter() - start_time
                logger.info(f"Executor: Finished in {duration:.4f}s with status: {exec_res.status}")
                exec_res.duration = duration
                return exec_res

        except Exception as e:
            logger.error(f"Executor: Execution lifecycle failed: {e}", exc_info=True)
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                logs=ExecutionLogs(stderr=str(e)),
                error=ExecutionError(
                    name=type(e).__name__, value=str(e), traceback=traceback.format_exc()
                ),
                duration=time.time() - start_time,
            )
        finally:
            if pooled_env:
                from .pool import pool_manager

                await pool_manager.release(pooled_env)

    async def _acquire_pooled_env(self, dependencies):
        if not ENABLE_ENV_POOLING or not dependencies:
            return None

        from .pool import pool_manager

        target_spec = None
        if any("torch" in d.lower() for d in dependencies):
            target_spec = "torch-gpu" if pool_manager.has_gpu else "torch-cpu"

        if target_spec:
            return await pool_manager.acquire(target_spec, timeout=1.0)
        return None

    def _prepare_workspace(self, tmpdir, code, test_code, mock_imports):
        tmp_path = Path(tmpdir)
        workspace = {
            "script_file": tmp_path / "solution.py",
            "harness_file": tmp_path / "harness.py",
            "result_file": tmp_path / "result.json",
        }
        workspace["script_file"].write_text(code, encoding="utf-8")
        harness_content = self._generate_harness(
            code, test_code, workspace["result_file"], mock_imports
        )
        workspace["harness_file"].write_text(harness_content, encoding="utf-8")
        return workspace

    def _build_command(self, pooled_env, harness_file, dependencies):
        if pooled_env:
            return [str(pooled_env.python_executable), str(harness_file)]

        offline = os.getenv("LOGICHIVE_OFFLINE", "true").lower() == "true"
        cmd = ["uv", "run", "--quiet"]
        if offline:
            cmd.append("--offline")
        cmd.append("--no-project")
        for dep in dependencies:
            cmd.extend(["--with", dep])
        cmd.extend(["python", str(harness_file)])
        return cmd

    async def _run_subprocess(self, cmd, cwd, timeout, memory_limit, result_file):
        process_env = {
            k: v
            for k, v in os.environ.items()
            if k
            in [
                "PATH",
                "SYSTEMROOT",
                "SystemDrive",
                "USERPROFILE",
                "APPDATA",
                "LOCALAPPDATA",
                "TEMP",
                "TMP",
                "USERNAME",
                "HOME",
                "HOMEDRIVE",
                "HOMEPATH",
                "ProgramData",
            ]
        }
        process_env.update({"PYTHONPATH": "", "PYTHONNOUSERSITE": "1"})

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=process_env,
        )

        # Track state across tasks
        state = {"memory_exceeded": False}
        done_event = asyncio.Event()
        monitor_task = asyncio.create_task(
            self._monitor_resources(process, memory_limit, done_event, state)
        )

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

            return self._parse_results(process.returncode, stdout, stderr, result_file)

        except asyncio.TimeoutError:
            self._kill_process_tree(process.pid)
            await process.wait()
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT, logs=ExecutionLogs(stderr="Execution timed out.")
            )
        finally:
            done_event.set()
            monitor_task.cancel()

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
                        logger.warning(f"Executor: Memory limit exceeded. Killing {process.pid}")
                        state["memory_exceeded"] = True
                        self._kill_process_tree(process.pid)
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Executor: Resource monitor crashed: {e}")

    def _parse_results(self, returncode, stdout, stderr, result_file) -> ExecutionResult:
        status = ExecutionStatus.SUCCESS if returncode == 0 else ExecutionStatus.FAILURE
        results, error = [], None

        if result_file.exists():
            try:
                raw = json.loads(result_file.read_text(encoding="utf-8"))
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
                logger.error(f"Executor: Failed to parse harness results: {e}")

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

    def _generate_harness(
        self, code: str, test_code: str, result_file: Path, mock_imports: list[str] | None = None
    ) -> str:
        """
        Generates a robust harness that executes the code and exports results as JSON.
        Modeled after Jupyter/E2B behavior.
        """
        # We escape the result path for the string template
        res_path = str(result_file).replace("\\", "\\\\")
        mock_imports = mock_imports or []
        mock_list_str = json.dumps(mock_imports)

        harness = f"""
import json
import traceback
import sys
from unittest.mock import MagicMock

# Result structure
results = {{
    "main_result": None,
    "error": None
}}

def block_network(*args, **kwargs):
    raise Exception("NETWORK_ACCESS_DENIED: LogicHive sandbox prevents network calls during verification.")

def apply_sandbox():
    import socket
    socket.socket = block_network
    socket.getaddrinfo = block_network
    # Also block common high-level libs if already imported
    for mod in ["urllib", "requests", "http.client"]:
        if mod in sys.modules:
            del sys.modules[mod]

def apply_mocks(mock_list):
    class LogicHiveSmartMock:
        def __getattr__(self, name):
            return LogicHiveSmartMock()
        def __call__(self, *args, **kwargs):
            return LogicHiveSmartMock()
        def __getitem__(self, key):
            return LogicHiveSmartMock()
        def __iter__(self):
            return iter([])
        def __repr__(self):
            return "<LogicHiveSmartMock>"

    for mod_name in mock_list:
        sys.modules[mod_name] = LogicHiveSmartMock()

def run_user_code():
    global results
    try:
        # 0. Apply runtime sandbox & mocks
        apply_sandbox()
        apply_mocks({mock_list_str})

        # 1. Execute the main code (defines functions/classes)
        exec({json.dumps(code)}, globals())

        # 2. Execute test code if provided
        if {json.dumps(test_code)}:
            # Tests are expected to raise AssertionError on failure
            exec({json.dumps(test_code)}, globals())
            if {mock_list_str}:
                results["main_result"] = f"Tests Passed (with Mocks: {{', '.join({mock_list_str})}})"
            else:
                results["main_result"] = "Tests Passed"
        else:
            # If no tests, we just check if it imports/defines correctly
            results["main_result"] = "Execution Successful"

    except Exception as e:
        type_name = type(e).__name__
        results["error"] = {{
            "name": type_name,
            "value": str(e),
            "traceback": traceback.format_exc()
        }}
        # We print to stderr so it shows up in logs too
        sys.stderr.write(traceback.format_exc())
        return False
    return True

success = run_user_code()

# Write results to the dedicated file
with open("{res_path}", "w", encoding="utf-8") as f:
    json.dump(results, f)

# Exit with non-zero if tests or execution failed
sys.exit(0 if success else 1)
"""
        return harness


# Auto-register
ExecutorFactory.register("python", EphemeralPythonExecutor())
"""
Implement EphemeralPythonExecutor
"""
