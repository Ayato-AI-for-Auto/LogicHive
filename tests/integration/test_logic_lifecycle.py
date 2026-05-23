import asyncio

import pytest

from core.exceptions import SyntaxValidationError, ValidationError
from orchestrator import do_get_verification_status, do_save_async


@pytest.mark.asyncio
async def test_save_flow_with_syntax_error(test_db):
    """
    Integration Test: Verifies that do_save_async rejects syntax errors synchronously.
    """
    name = "bad_syntax_func"
    code = "def oops(\n    print('missing paren')"  # Syntax Error

    with pytest.raises(SyntaxValidationError) as excinfo:
        await do_save_async(
            name=name, code=code, description="Should fail synchronously", language="python"
        )

    assert "Python Syntax Error" in str(excinfo.value)
    print(f"\n[INTEGRATION TEST] Correctly caught synchronous syntax error: {excinfo.value}")


@pytest.mark.asyncio
async def test_successful_save_lifecycle(test_db):
    """
    Integration Test: Verifies a full successful lifecycle from save to verified status.
    Uses FakeLogicIntelligence (Mocking allowed).
    """
    name = "good_math_func"
    code = "def add(a, b): return a + b"
    test_code = "assert add(1, 2) == 3"

    # 1. Save (Synchronous part)
    success = await do_save_async(
        name=name,
        code=code,
        description="A simple addition function",
        test_code=test_code,
        project="integration_test",
    )
    assert success is True

    # 2. Check initial status
    status_data = await do_get_verification_status(name, project="integration_test")
    assert status_data["status"] in ["pending", "verified"]

    # 3. Wait for background verification (using a small timeout since it's mocked)
    for _ in range(5):
        await asyncio.sleep(0.5)
        status_data = await do_get_verification_status(name, project="integration_test")
        if status_data["status"] == "verified":
            break

    assert status_data["status"] == "verified"
    assert status_data["score"] >= 70
    print(f"\n[INTEGRATION TEST] Lifecycle successful. Final Status: {status_data['status']}")


@pytest.mark.asyncio
async def test_duplicate_logic_rejection(test_db):
    """
    Integration Test: Verifies that identical logic is rejected even with different names.
    """
    code = "def constant(): return 42"

    await do_save_async(name="first", code=code, description="First one", project="dup_test")

    with pytest.raises(ValidationError) as excinfo:
        await do_save_async(
            name="second", code=code, description="Duplicate logic", project="dup_test"
        )

    assert "Asset with identical logic is already registered" in str(excinfo.value)
    print("\n[INTEGRATION TEST] Correctly rejected duplicate logic.")
