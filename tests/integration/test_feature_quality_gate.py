import asyncio

import pytest

from core.exceptions import SyntaxValidationError
import pytest

from orchestrator import do_get_verification_status, do_save_async
from storage import sqlite_api

@pytest.mark.asyncio
async def test_integration_save_valid_function(test_db):
    """INTEGRATION: Orchestrator should save and eventually verify a valid function."""
    name = "integ_valid_func"
    code = "def multiply(a, b): return a * b"
    test_code = "assert multiply(2, 3) == 6"

    # 1. Trigger Save (which returns immediately after DB insert)
    accepted = await do_save_async(
        name=name, code=code, description="integration test", test_code=test_code, project="integ"
    )
    assert accepted is True

    # Wait for background verification to complete
    for _ in range(20):
        status_data = await do_get_verification_status(name, project="integ")
        if status_data["status"] != "pending":
            break
        await asyncio.sleep(0.5)

    assert status_data["status"] == "verified", f"Should be verified, got: {status_data}"


@pytest.mark.asyncio
async def test_integration_save_syntax_error(test_db):
    """INTEGRATION: Orchestrator should reject immediately on syntax error."""
    name = "integ_syntax_func"
    code = "def broken(:"

    with pytest.raises(SyntaxValidationError):
        await do_save_async(name=name, code=code, test_code="", project="integ")


@pytest.mark.asyncio
async def test_integration_save_quality_rejection(test_db):
    """INTEGRATION: Orchestrator should reject logic with no tests or empty logic."""
    name = "integ_empty_func"
    code = "def empty(): pass"
    test_code = "assert True"  # Quality theater

    accepted = await do_save_async(
        name=name, code=code, description="", test_code=test_code, project="integ"
    )
    assert accepted is True

    # Wait for background verification
    for _ in range(20):
        status_data = await do_get_verification_status(name, project="integ")
        if status_data["status"] != "pending":
            break
        await asyncio.sleep(0.5)

    # Check Status - should be rejected/failed
    assert status_data["status"] == "failed"


@pytest.mark.asyncio
async def test_integration_draft_mode(test_db):
    """INTEGRATION: Lack of tests allows saving as Draft but not Verified."""
    name = "integ_draft_func"
    code = "def draft(): return 'draft'"
    test_code = ""  # No test

    accepted = await do_save_async(
        name=name, code=code, description="", test_code=test_code, project="integ"
    )
    assert accepted is True

    for _ in range(20):
        status_data = await do_get_verification_status(name, project="integ")
        if status_data["status"] != "pending":
            break
        await asyncio.sleep(0.5)

    assert status_data["status"] in [
        "failed",
        "error",
    ]  # A draft without a valid test fails verification but remains in the vault

    # Let's check DB to ensure it was saved despite failing
    f_data = await sqlite_api.sqlite_storage.get_function_by_name(name, project="integ")
    assert f_data is not None
    assert f_data["verification_status"] in ["failed", "error"]
