
import pytest

from core.execution.base import ExecutionStatus
from core.execution.python import EphemeralPythonExecutor


@pytest.fixture
def executor():
    return EphemeralPythonExecutor()


@pytest.mark.asyncio
async def test_sandbox_network_blocking(executor):
    """
    Verifies that the sandbox blocks network access (socket.connect).
    """
    code = """
import socket
def check_leak():
    # This should raise Exception from the harness's block_network
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return "Should have failed"
"""
    test_code = "check_leak()"

    result = await executor.execute(code, test_code=test_code)

    # The harness catch the Exception and marks status as FAILURE
    assert result.status == ExecutionStatus.FAILURE
    assert "NETWORK_ACCESS_DENIED" in result.error.value




@pytest.mark.asyncio
async def test_execution_timeout_logic(executor):
    """Verifies that infinite loops are caught by the timeout."""
    # We use a real execution but with a very short timeout to test the process killing
    code = "import time\ndef infinite():\n    while True: time.sleep(0.1)"
    test_code = "infinite()"

    # Run with a 1 second timeout
    result = await executor.execute(code, test_code=test_code, timeout=1)

    assert result.status == ExecutionStatus.TIMEOUT
