import asyncio
import os
import sqlite3
import pytest
from core.exceptions import ValidationError
from orchestrator import do_save_async, do_get_verification_status
from storage.sqlite_api import sqlite_storage


@pytest.mark.asyncio
async def test_pipeline_versioning_and_history_archival(test_db):
    """Integration: Test registering same hash vs different hash, and verify SQLite history archiving."""
    project = "pipeline_test"
    name = "calculate_sum"
    code_v1 = "def calculate_sum(a, b):\n    return a + b"
    test_code = "assert calculate_sum(2, 3) == 5"

    # 1. First registration (V1)
    success = await do_save_async(
        name=name, code=code_v1, description="adds two numbers", test_code=test_code, project=project
    )
    assert success is True

    # Get from storage and check version is 1
    func_v1 = await sqlite_storage.get_function_by_name(name, project=project)
    assert func_v1 is not None
    assert func_v1["version"] == 1

    # 2. Second registration with SAME code hash (should raise ValidationError)
    with pytest.raises(ValidationError) as exc_info:
        await do_save_async(
            name=name, code=code_v1, description="adds two numbers - updated desc", test_code=test_code, project=project
        )
    assert "already exists" in str(exc_info.value)

    # 3. Third registration with DIFFERENT code (should increment version to 2 and archive V1)
    code_v2 = "def calculate_sum(a, b):\n    # Optimized version\n    return sum([a, b])"
    success = await do_save_async(
        name=name, code=code_v2, description="adds two numbers - v2 optimized", test_code=test_code, project=project
    )
    assert success is True

    func_v2 = await sqlite_storage.get_function_by_name(name, project=project)
    assert func_v2["version"] == 2

    # 4. Directly query database history table to verify V1 was archived (情報の裏取り)
    db_path = os.environ["SQLITE_DB_PATH"]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM logichive_function_history WHERE name = ? AND project = ?", (name, project))
    history_records = cursor.fetchall()
    
    # We should have exactly 1 archived version (the original V1)
    assert len(history_records) == 1
    archive = history_records[0]
    assert archive["version"] == 1
    assert archive["code"] == code_v1
    assert archive["description"] == "adds two numbers" # The latest state of V1
    conn.close()


@pytest.mark.asyncio
async def test_pipeline_verification_failure_injection(test_db):
    """Integration: Inject verification failures and check if DB state is correctly updated to 'failed'."""
    project = "pipeline_test"
    name = "flaky_function"
    # 'break_eval' in code triggers FakeLogicIntelligence to return quality score = 10 (fails gate)
    code = "def flaky_function():\n    # break_eval to trigger low quality score\n    return 'flaky'"
    test_code = "assert flaky_function() == 'flaky'"

    success = await do_save_async(
        name=name, code=code, description="flaky quality gate test", test_code=test_code, project=project
    )
    assert success is True

    # Wait for the background worker to run verification and fail it
    status_data = None
    for _ in range(20):
        status_data = await do_get_verification_status(name, project=project)
        if status_data["status"] != "pending":
            break
        await asyncio.sleep(0.1)

    assert status_data is not None
    assert status_data["status"] == "failed"

    # Directly verify DB states to ensure 'failed' status and score are logged (情報の裏取り)
    db_path = os.environ["SQLITE_DB_PATH"]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT verification_status, reliability_score FROM logichive_functions WHERE name = ? AND project = ?", (name, project))
    row = cursor.fetchone()
    assert row is not None
    assert row["verification_status"] == "failed"
    assert row["reliability_score"] < 50.0  # Quality score of 10 was recorded

    conn.close()
