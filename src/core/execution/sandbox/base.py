from abc import ABC, abstractmethod

from core.execution.base import ExecutionResult


class BaseSandbox(ABC):
    """
    Interface for language-agnostic code execution sandboxes.
    Decoupled from specific language execution lifecycles (like Python virtual environments).
    """

    @abstractmethod
    async def execute_command(
        self,
        cmd: list[str],
        cwd: str,
        env: dict[str, str] | None = None,
        timeout: float = 10.0,
        memory_limit_mb: int = 256,
        result_file: str | None = None,
    ) -> ExecutionResult:
        """
        Executes a command inside the sandbox.

        Args:
            cmd: Command and its arguments to run.
            cwd: Working directory for the process.
            env: Optional environment variables.
            timeout: Maximum execution time in seconds.
            memory_limit_mb: Hard memory limit in Megabytes.
            result_file: Optional path to a JSON file containing structured harness outputs.
        """
        pass
