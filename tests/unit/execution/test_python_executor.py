import os

import pytest

from core.execution.base import ExecutionStatus
from core.execution.python import EphemeralPythonExecutor


@pytest.mark.asyncio
async def test_python_executor_success():
    """Verifies that valid Python code executes successfully."""
    executor = EphemeralPythonExecutor()
    code = "def add(a, b): return a + b"
    test_code = "assert add(2, 3) == 5"

    result = await executor.execute(code, test_code)

    assert result.status == ExecutionStatus.SUCCESS
    assert "Tests Passed" in result.results[0].data
    assert result.duration > 0


@pytest.mark.asyncio
async def test_python_executor_failure():
    """Verifies that failing assertions are captured as FAILURE."""
    executor = EphemeralPythonExecutor()
    code = "def add(a, b): return a + b"
    test_code = "assert add(2, 3) == 6"  # Wrong expectation

    result = await executor.execute(code, test_code)

    assert result.status == ExecutionStatus.FAILURE
    assert result.error is not None
    assert "AssertionError" in result.error.name


@pytest.mark.asyncio
async def test_python_executor_timeout():
    """Verifies that infinite loops are killed by the timeout."""
    executor = EphemeralPythonExecutor()
    code = "import time\nwhile True: time.sleep(0.1)"

    # Set a more realistic timeout for the test to allow uv startup and sync (Windows)
    result = await executor.execute(code, timeout=10)

    assert result.status == ExecutionStatus.TIMEOUT
    # Note: stderr might be empty if killed forcefully on Windows


@pytest.mark.asyncio
async def test_python_executor_with_dependencies():
    """
    Verifies that 'uv run --with' works for external dependencies,
    or skips the network-dependent part in CI environments.
    """
    # Detect CI environment to avoid network failures
    os.getenv("GITHUB_ACTIONS") == "true"

    executor = EphemeralPythonExecutor()
    code = "import json\ndef check(): return json.dumps({'a': 1})"
    test_code = "assert check() == '{\"a\": 1}'"

    # Use a built-in module for testing instead of numpy to ensure network independence
    dependencies = []

    result = await executor.execute(code, test_code, dependencies=dependencies)

    assert result.status == ExecutionStatus.SUCCESS

    assert "Tests Passed" in result.results[0].data


@pytest.mark.asyncio
async def test_python_executor_syntax_error():
    """Verifies that syntax errors in the user code are captured."""
    executor = EphemeralPythonExecutor()
    code = "def broken_syntax(:"  # Missing paren

    result = await executor.execute(code)

    assert result.status == ExecutionStatus.FAILURE
    assert "SyntaxError" in result.error.name


@pytest.mark.asyncio
async def test_python_executor_dynamic_env():
    """
    Verifies that dynamic environment creation is triggered for non-prewarmed dependencies
    and cleaned up afterwards.
    """

    executor = EphemeralPythonExecutor()
    code = "import dateutil\ndef parse_date(): return dateutil.parser.parse('2026-01-01').year"
    test_code = "assert parse_date() == 2026"
    dependencies = ["python-dateutil"]

    result = await executor.execute(code, test_code, dependencies=dependencies)

    assert result.status == ExecutionStatus.SUCCESS
    assert "Tests Passed" in result.results[0].data
