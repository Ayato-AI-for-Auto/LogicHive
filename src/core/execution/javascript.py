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


class EphemeralJavaScriptExecutor(BaseExecutor):
    """
    Executes JavaScript and TypeScript code in an isolated sandbox using Node.js.
    """

    def __init__(self):
        self.name = "javascript"
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
            f"JS/TS Executor: Starting execution [timeout={timeout}s, memory={memory_limit_mb}MB]"
        )
        start_time = time.perf_counter()
        language = kwargs.get("language", "javascript").lower()

        # Check Node.js availability
        node_check = await self._is_node_available()
        if not node_check:
            err_msg = "Execution failed: Node.js runtime is not installed or not found in system PATH."
            logger.error(err_msg)
            return ExecutionResult(
                status=ExecutionStatus.FAILURE,
                logs=ExecutionLogs(stderr=err_msg),
                error=ExecutionError(
                    name="RuntimeError", value=err_msg, traceback=""
                ),
                duration=time.perf_counter() - start_time,
            )

        try:
            with tempfile.TemporaryDirectory(prefix="logichive_js_") as tmpdir:
                workspace = self._prepare_workspace(tmpdir, code, test_code, language)

                # Command: node runs the harness
                cmd = ["node"]
                if language == "typescript":
                    # Node v22 supports running TypeScript via --experimental-strip-types
                    cmd.append("--experimental-strip-types")
                cmd.append(str(workspace["harness_file"]))

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
            logger.error(f"JS/TS Executor: Lifecycle failed: {e}", exc_info=True)
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                logs=ExecutionLogs(stderr=str(e)),
                error=ExecutionError(
                    name=type(e).__name__, value=str(e), traceback=traceback.format_exc()
                ),
                duration=time.perf_counter() - start_time,
            )

    async def _is_node_available(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                "node",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False

    def _prepare_workspace(self, tmpdir: str, code: str, test_code: str, language: str) -> dict[str, Path]:
        tmp_path = Path(tmpdir)
        ext = "ts" if language == "typescript" else "js"

        workspace = {
            "script_file": tmp_path / f"solution.{ext}",
            "harness_file": tmp_path / f"harness.{ext}",
            "result_file": tmp_path / "result.json",
        }

        workspace["script_file"].write_text(code, encoding="utf-8")
        harness_content = self._generate_harness(test_code, workspace["result_file"], ext)
        workspace["harness_file"].write_text(harness_content, encoding="utf-8")
        return workspace

    def _generate_harness(self, test_code: str, result_file: Path, ext: str) -> str:
        res_path = str(result_file).replace("\\", "\\\\")

        # Build node.js assert harness
        harness = f"""
const fs = require('fs');
const assert = require('assert');

let results = {{
    main_result: null,
    error: null
}};

async function runTest() {{
    try {{
        // Load solution module using dynamic import (supports ESM and CommonJS)
        const solutionModule = await import('./solution.{ext}');
        const solution = solutionModule.default && Object.keys(solutionModule.default).length > 0
            ? {{ ...solutionModule, ...solutionModule.default }}
            : solutionModule;

        // Execute test code in block wrapper
        const testFn = async function(solution, assert) {{
            {test_code}
        }};

        await testFn(solution, assert);
        results.main_result = "All JavaScript tests passed successfully.";
    }} catch (e) {{
        results.error = {{
            name: e.name || "AssertionError",
            value: e.message || String(e),
            traceback: e.stack || String(e)
        }};
    }} finally {{
        fs.writeFileSync('{res_path}', JSON.stringify(results), 'utf8');
    }}
}}

runTest();
"""
        return harness


# Auto-register
js_executor = EphemeralJavaScriptExecutor()
ExecutorFactory.register("javascript", js_executor)
ExecutorFactory.register("typescript", js_executor)
ClassEphemeralJavaScriptExecutor = "EphemeralJavaScriptExecutor"
