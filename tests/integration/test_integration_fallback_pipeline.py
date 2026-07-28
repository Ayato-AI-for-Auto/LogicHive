from unittest.mock import patch

import pytest

from core.evaluation.manager import EvaluationManager
from core.execution.base import ExecutionLogs, ExecutionStatus
from core.execution.base import ExecutionResult as ExecRes


@pytest.mark.asyncio
async def test_evaluation_manager_with_php_missing_runtime():
    """
    Verifies that when PHP runtime is missing, the PHP executor returns FAILURE,
    which EvaluationManager processes into a score of 0.0 with the specific RuntimeError.
    """
    manager = EvaluationManager()

    code = "function test() { return 1; }"
    test_code = "assert(test() === 1);"

    # Run php evaluation with php missing on PATH by mocking detection
    with patch("core.execution.php.EphemeralPhpExecutor._is_php_available", return_value=False):
        results = await manager.evaluate_all(
            code=code, language="php", test_code=test_code, description="PHP Asset"
        )

    assert results["score"] == 0.0
    assert "php cli is not installed" in results["reason"].lower()


@pytest.mark.asyncio
async def test_evaluation_manager_with_c_missing_runtime():
    manager = EvaluationManager()

    code = "int test() { return 1; }"
    test_code = 'assert_c(test() == 1, "error");'

    with patch("core.execution.c.EphemeralCExecutor._find_compiler", return_value=None):
        results = await manager.evaluate_all(
            code=code, language="c", test_code=test_code, description="C Asset"
        )

    assert results["score"] == 0.0
    assert "no c compiler" in results["reason"].lower()


@pytest.mark.asyncio
async def test_evaluation_manager_corrupted_harness_json():
    """
    Simulates a harsh execution where the JS sandbox starts and completes,
    but the result JSON file is missing or corrupted.
    """
    manager = EvaluationManager()

    code = "console.log('hello');"
    test_code = "assert(true);"

    # Mock the sandbox's execute_command to return SUCCESS but write corrupted or missing result file
    # We patch WindowsNativeSandbox.execute_command
    with patch("core.execution.sandbox.windows.WindowsNativeSandbox.execute_command") as mock_exec:
        # Mock success return but results list will be empty because result_file wasn't created or parsed
        mock_exec.return_value = ExecRes(
            status=ExecutionStatus.FAILURE,
            logs=ExecutionLogs(stdout="ran but crashed", stderr="Parse error"),
            duration=0.1,
        )

        results = await manager.evaluate_all(
            code=code, language="javascript", test_code=test_code, description="JS Corrupted test"
        )

        assert results["score"] == 0.0
        assert "logic error" in results["reason"].lower()
