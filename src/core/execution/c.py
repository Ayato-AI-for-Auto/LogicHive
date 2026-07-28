import asyncio
import os
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


class EphemeralCExecutor(BaseExecutor):
    """
    Executes C code by compiling via gcc/clang/cl and running the binary in the sandbox.
    """

    def __init__(self):
        self.name = "c"
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
            f"C Executor: Starting execution [timeout={timeout}s, memory={memory_limit_mb}MB]"
        )
        start_time = time.perf_counter()

        # Find available compiler
        compiler = await self._find_compiler()
        if not compiler:
            err_msg = "Execution failed: No C compiler (gcc, clang, or cl) found in system PATH."
            logger.error(err_msg)
            return ExecutionResult(
                status=ExecutionStatus.FAILURE,
                logs=ExecutionLogs(stderr=err_msg),
                error=ExecutionError(name="RuntimeError", value=err_msg, traceback=""),
                duration=time.perf_counter() - start_time,
            )

        try:
            with tempfile.TemporaryDirectory(prefix="logichive_c_") as tmpdir:
                workspace = self._prepare_workspace(tmpdir, code, test_code)

                # Step 1: Compile
                binary_name = "harness.exe" if os.name == "nt" else "./harness"
                if compiler == "cl":
                    # MSVC compiler
                    compile_cmd = ["cl", "/Fe" + binary_name, str(workspace["harness_file"])]
                else:
                    # gcc or clang
                    compile_cmd = [compiler, "-o", binary_name, str(workspace["harness_file"])]

                compile_proc = await asyncio.create_subprocess_exec(
                    *compile_cmd,
                    cwd=tmpdir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout_c, stderr_c = await compile_proc.communicate()
                if compile_proc.returncode != 0:
                    compile_err = stderr_c.decode("utf-8", errors="replace") + stdout_c.decode(
                        "utf-8", errors="replace"
                    )
                    return ExecutionResult(
                        status=ExecutionStatus.FAILURE,
                        logs=ExecutionLogs(stderr=compile_err),
                        error=ExecutionError(
                            name="CompileError", value="Compilation failed", traceback=compile_err
                        ),
                        duration=time.perf_counter() - start_time,
                    )

                # Step 2: Execute Binary under Sandbox
                cmd = [os.path.join(tmpdir, binary_name)]
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
            logger.error(f"C Executor: Lifecycle failed: {e}", exc_info=True)
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                logs=ExecutionLogs(stderr=str(e)),
                error=ExecutionError(
                    name=type(e).__name__, value=str(e), traceback=traceback.format_exc()
                ),
                duration=time.perf_counter() - start_time,
            )

    async def _find_compiler(self) -> str | None:
        for comp in ["gcc", "clang", "cl"]:
            try:
                proc = await asyncio.create_subprocess_exec(
                    comp,
                    "--version" if comp != "cl" else "/?",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                if proc.returncode == 0 or (comp == "cl" and proc.returncode == 0):
                    return comp
            except Exception:
                continue
        return None

    def _prepare_workspace(self, tmpdir: str, code: str, test_code: str) -> dict[str, Path]:
        tmp_path = Path(tmpdir)
        workspace = {
            "harness_file": tmp_path / "harness.c",
            "result_file": tmp_path / "result.json",
        }

        harness_content = self._generate_harness(code, test_code, workspace["result_file"])
        workspace["harness_file"].write_text(harness_content, encoding="utf-8")
        return workspace

    def _generate_harness(self, code: str, test_code: str, result_file: Path) -> str:
        res_path = str(result_file).replace("\\", "\\\\")

        # Build self-contained C harness
        harness = f"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// User C code
{code}

// Main test entry
int main() {{
    FILE* f = fopen("{res_path}", "w");
    if (!f) {{
        fprintf(stderr, "Failed to open result file\\n");
        return 1;
    }}

    // Inject custom assertions for the test script
    #define assert_c(expr, msg) \\
        if (!(expr)) {{ \\
            fprintf(f, "{{\\"main_result\\":null,\\"error\\":{{\\"name\\":\\"AssertionError\\",\\"value\\":\\"%s\\",\\"traceback\\":\\"\\"}}}}", msg); \\
            fclose(f); \\
            exit(1); \\
        }}

    // Run tests
    {test_code}

    fprintf(f, "{{\\"main_result\\":\\"All C tests passed successfully.\\",\\"error\\":null}}");
    fclose(f);
    return 0;
}}
"""
        return harness


# Auto-register
ExecutorFactory.register("c", EphemeralCExecutor())
