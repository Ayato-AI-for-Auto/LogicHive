import os
import sqlite3

import pytest

import core.config
from storage import sqlite_api


@pytest.mark.asyncio
async def test_db_initialization(test_db):
    """UNIT: Verify that the DB is properly created with required tables."""
    db_path = core.config.SQLITE_DB_PATH
    assert os.path.exists(db_path)

    # Actually query the physical DB to ensure table exists
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='logichive_functions'"
    )
    table = cursor.fetchone()
    conn.close()

    assert table is not None, "logichive_functions table should exist."


@pytest.mark.asyncio
async def test_upsert_and_fetch_function(test_db):
    """UNIT: Verify inserting a function and retrieving it with exact data match."""
    name = "unit_upsert_test"
    code = "def test(): return 1"

    # Insert
    await sqlite_api.sqlite_storage.upsert_function(
        {
            "name": name,
            "code": code,
            "description": "A unit test function",
            "tags": ["unit", "test"],
            "language": "python",
            "dependencies": [],
            "reliability_score": 0.95,
            "verification_status": "verified",
            "verification_report": '{"reason": "passed"}',
            "project": "default",
            "test_code": "",
            "is_draft": False,
            "env_fingerprint": "test_env",
        }
    )

    # Retrieve
    func = await sqlite_api.sqlite_storage.get_function_by_name(name, project="default")

    # Verify exact match
    assert func is not None
    assert func["name"] == name
    assert func["code"] == code
    assert "unit" in func["tags"]
    assert func["reliability_score"] == 0.95
    assert func["verification_status"] == "verified"


@pytest.mark.asyncio
async def test_delete_function(test_db):
    """UNIT: Verify deleting a function actually removes it from DB."""
    name = "unit_delete_test"
    await sqlite_api.sqlite_storage.upsert_function(
        {
            "name": name,
            "code": "pass",
            "description": "",
            "tags": [],
            "language": "python",
            "dependencies": [],
            "reliability_score": 0,
            "verification_status": "pending",
            "verification_report": "",
            "project": "default",
            "test_code": "",
            "is_draft": True,
        }
    )

    # Confirm it exists
    assert await sqlite_api.sqlite_storage.get_function_by_name(name) is not None

    # Delete
    success = await sqlite_api.sqlite_storage.delete_function(name, "default")
    assert success is True

    # Confirm it's gone
    assert await sqlite_api.sqlite_storage.get_function_by_name(name) is None
