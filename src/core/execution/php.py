import asyncio
import tempfile
import time
import traceback
from pathlib import Path

from core.execution.sandbox.windows import WindowsNativeSandbox
from core.logging_config import get_logger

from .base import (
    BaseExecutor,
    ExecutionError,
    ExecutionLogs,
    ExecutionResult,
    ExecutionStatus,
)
from .factory import ExecutorFactory

logger = get_logger(__name__)


class EphemeralPhpExecutor(BaseExecutor):
    """
    Executes PHP code using PHP CLI in the sandbox.
    """

    def __init__(self):
        self.name = "php"
        self.sandbox = WindowsNativeSandbox()

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
            f"PHP Executor: Starting execution [timeout={timeout}s, memory={memory_limit_mb}MB]"
        )
        start_time = time.perf_counter()

        # Check PHP availability
        php_check = await self._is_php_available()
        if not php_check:
            err_msg = "Execution failed: PHP CLI is not installed or not found in system PATH."
            logger.error(err_msg)
            return ExecutionResult(
                status=ExecutionStatus.FAILURE,
                logs=ExecutionLogs(stderr=err_msg),
                error=ExecutionError(name="RuntimeError", value=err_msg, traceback=""),
                duration=time.perf_counter() - start_time,
            )

        try:
            with tempfile.TemporaryDirectory(prefix="logichive_php_") as tmpdir:
                workspace = self._prepare_workspace(tmpdir, code, test_code)

                # Command: php runs the harness
                cmd = ["php", str(workspace["harness_file"])]

                exec_res = await self.sandbox.execute_command(
                    cmd=cmd,
                    cwd=tmpdir,
                    timeout=timeout,
                    memory_limit_mb=memory_limit_mb,
                    result_file=str(workspace["result_file"]),
                )

                duration = time.perf_counter() - start_time
                exec_res.duration = duration
                return exec_res

        except Exception as e:
            logger.error(f"PHP Executor: Lifecycle failed: {e}", exc_info=True)
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                logs=ExecutionLogs(stderr=str(e)),
                error=ExecutionError(
                    name=type(e).__name__, value=str(e), traceback=traceback.format_exc()
                ),
                duration=time.perf_counter() - start_time,
            )

    async def _is_php_available(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                "php",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False

    def _prepare_workspace(self, tmpdir: str, code: str, test_code: str) -> dict[str, Path]:
        tmp_path = Path(tmpdir)
        workspace = {
            "script_file": tmp_path / "solution.php",
            "harness_file": tmp_path / "harness.php",
            "result_file": tmp_path / "result.json",
        }

        # Make sure solution has opening <?php tag if not present
        if not code.strip().startswith("<?php"):
            code = "<?php\n" + code

        workspace["script_file"].write_text(code, encoding="utf-8")
        harness_content = self._generate_harness(test_code, workspace["result_file"])
        workspace["harness_file"].write_text(harness_content, encoding="utf-8")
        return workspace

    def _generate_harness(self, test_code: str, result_file: Path) -> str:
        res_path = str(result_file).replace("\\", "\\\\")

        harness = f"""<?php
$results = [
    "main_result" => null,
    "error" => null
];

try {{
    require_once 'solution.php';

    // Execute test code block
    {test_code}

    $results["main_result"] = "All PHP tests passed successfully.";
}} catch (Throwable $t) {{
    $results["error"] = [
        "name" => get_class($t),
        "value" => $t->getMessage(),
        "traceback" => $t->getTraceAsString()
    ];
}}

file_put_contents('{res_path}', json_encode($results, JSON_PRETTY_PRINT));
"""
        return harness


# Auto-register
ExecutorFactory.register("php", EphemeralPhpExecutor())
