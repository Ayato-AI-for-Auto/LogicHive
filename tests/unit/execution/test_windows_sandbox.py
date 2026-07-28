import os
import sys

import pytest

from core.execution.base import ExecutionStatus
from core.execution.sandbox.windows import WindowsNativeSandbox


@pytest.fixture
def sandbox():
    return WindowsNativeSandbox()


@pytest.mark.asyncio
async def test_sandbox_simple_execution(sandbox):
    """Verifies that the sandbox runs a command and captures stdout."""
    # Run simple python command printing hello
    cmd = [sys.executable, "-c", "print('hello from sandbox')"]
    result = await sandbox.execute_command(
        cmd=cmd,
        cwd=os.getcwd(),
        timeout=5,
    )
    assert result.status == ExecutionStatus.SUCCESS
    assert "hello from sandbox" in result.logs.stdout.strip()


@pytest.mark.asyncio
async def test_sandbox_timeout(sandbox):
    """Verifies that the sandbox enforces execution timeouts."""
    cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
    result = await sandbox.execute_command(
        cmd=cmd,
        cwd=os.getcwd(),
        timeout=1,
    )
    assert result.status == ExecutionStatus.TIMEOUT
    assert "timed out" in result.logs.stderr.lower()


@pytest.mark.asyncio
async def test_sandbox_memory_limit(sandbox):
    """Verifies that the sandbox catches OOM / memory limits via Job Object or fallback."""
    # Rapidly consume memory
    cmd = [
        sys.executable,
        "-c",
        "import time; data = bytearray(80 * 1024 * 1024); time.sleep(5)",
    ]
    result = await sandbox.execute_command(
        cmd=cmd,
        cwd=os.getcwd(),
        timeout=10,
        memory_limit_mb=40,  # limit to 40MB
    )
    assert result.status == ExecutionStatus.MEMORY_LIMIT
    assert (
        "memory limit exceeded" in result.logs.stderr.lower()
        or "limit of 40mb exceeded" in result.logs.stderr.lower()
    )
