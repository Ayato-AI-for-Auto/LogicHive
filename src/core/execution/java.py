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


class EphemeralJavaExecutor(BaseExecutor):
    """
    Executes Java code by compiling with javac and executing with java in the sandbox.
    """

    def __init__(self):
        self.name = "java"
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
            f"Java Executor: Starting execution [timeout={timeout}s, memory={memory_limit_mb}MB]"
        )
        start_time = time.perf_counter()

        # Check Java availability
        java_check = await self._is_java_available()
        if not java_check:
            err_msg = "Execution failed: JDK (javac/java) is not installed or not found in system PATH."
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
            with tempfile.TemporaryDirectory(prefix="logichive_java_") as tmpdir:
                workspace = self._prepare_workspace(tmpdir, code, test_code)

                # Step 1: Compile Harness.java
                compile_proc = await asyncio.create_subprocess_exec(
                    "javac",
                    str(workspace["harness_file"]),
                    cwd=tmpdir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout_c, stderr_c = await compile_proc.communicate()
                if compile_proc.returncode != 0:
                    compile_err = stderr_c.decode("utf-8", errors="replace")
                    return ExecutionResult(
                        status=ExecutionStatus.FAILURE,
                        logs=ExecutionLogs(stderr=compile_err),
                        error=ExecutionError(
                            name="CompileError", value="Compilation failed", traceback=compile_err
                        ),
                        duration=time.perf_counter() - start_time,
                    )

                # Step 2: Execute Harness via Java Sandbox
                cmd = ["java", "Harness"]
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
            logger.error(f"Java Executor: Lifecycle failed: {e}", exc_info=True)
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                logs=ExecutionLogs(stderr=str(e)),
                error=ExecutionError(
                    name=type(e).__name__, value=str(e), traceback=traceback.format_exc()
                ),
                duration=time.perf_counter() - start_time,
            )

    async def _is_java_available(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                "javac",
                "-version",
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
            "harness_file": tmp_path / "Harness.java",
            "result_file": tmp_path / "result.json",
        }

        harness_content = self._generate_harness(code, test_code, workspace["result_file"])
        workspace["harness_file"].write_text(harness_content, encoding="utf-8")
        return workspace

    def _generate_harness(self, code: str, test_code: str, result_file: Path) -> str:
        res_path = str(result_file).replace("\\", "\\\\")

        # Build self-contained java test class
        harness = f"""
import java.io.FileWriter;
import java.io.IOException;

public class Harness {{

    // User solution code
    {code}

    public static void main(String[] args) {{
        String resultJson = "{{\\"main_result\\":null,\\"error\\":null}}";
        try {{
            // Test code run
            {test_code}

            resultJson = "{{\\"main_result\\":\\"All Java tests passed successfully.\\",\\"error\\":null}}";
        }} catch (Throwable t) {{
            String msg = t.getMessage() != null ? t.getMessage() : t.toString();
            msg = msg.replace("\\"", "\\\\\\"").replace("\\n", " ");
            resultJson = "{{\\"main_result\\":null,\\"error\\":{{\\"name\\":\\"" + t.getClass().getSimpleName() + "\\",\\"value\\":\\"" + msg + "\\",\\"traceback\\":\\"\\"}}}}";
        }}

        try (FileWriter fw = new FileWriter("{res_path}")) {{
            fw.write(resultJson);
        }} catch (IOException e) {{
            System.err.println("Failed to write result: " + e.getMessage());
        }}
    }}
}}
"""
        return harness


# Auto-register
ExecutorFactory.register("java", EphemeralJavaExecutor())
ClassEphemeralJavaExecutor = "EphemeralJavaExecutor"
