import os
import sqlite3

import aiosqlite
import pytest

from core.db import get_db_connection, retry_on_db_lock
from storage.sqlite_api import SqliteStorage, _safe_json_loads


@pytest.mark.asyncio
async def test_get_db_connection_initializes_schema(db_isolation):
    """Verify get_db_connection() initializes correct SQLite schemas and tables."""
    # Acquire database connection
    db = await get_db_connection()
    assert isinstance(db, aiosqlite.Connection)

    # Directly check database using python's standard sqlite3 (direct DB verification)
    db_path = os.environ["SQLITE_DB_PATH"]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verify tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    assert "logichive_functions" in tables
    assert "logichive_function_history" in tables

    # Verify column structures of logichive_functions
    cursor.execute("PRAGMA table_info(logichive_functions)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    assert "id" in columns
    assert "project" in columns
    assert "name" in columns
    assert "code" in columns
    assert "reliability_score" in columns
    assert "verification_status" in columns

    conn.close()


@pytest.mark.asyncio
async def test_safe_json_loads():
    """Verify JSON helper safely parses valid/invalid inputs."""
    assert _safe_json_loads('{"a": 1}', "test_field") == {"a": 1}
    assert _safe_json_loads("", "test_field") == ""
    # Returns original string on decode error
    assert _safe_json_loads("{invalid}", "test_field") == "{invalid}"


@pytest.mark.asyncio
async def test_sqlite_storage_direct_verification(db_isolation):
    """Upsert function data and directly access SQLite via python sqlite3 to verify the stored state."""
    storage = SqliteStorage()
    func_data = {
        "id": "123",
        "name": "add_numbers",
        "project": "math_library",
        "code": "def add(a, b): return a + b",
        "description": "Adds two numbers.",
        "tags": ["math", "utility"],
        "reliability_score": 95.5,
        "test_metrics": {"passed": 3},
        "code_hash": "hash_abc123",
        "dependencies": ["numpy"],
        "test_code": "assert add(1, 2) == 3",
        "env_fingerprint": {"python": "3.11"},
        "verification_status": "verified",
        "verification_report": {"gate": "passed"}
    }

    # Perform upsert
    success = await storage.upsert_function(func_data)
    assert success is True

    # Information verification via direct sqlite3 query (情報の裏取り)
    db_path = os.environ["SQLITE_DB_PATH"]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM logichive_functions WHERE name = ? AND project = ?", ("add_numbers", "math_library"))
    row = cursor.fetchone()
    assert row is not None

    # Check database fields match exactly what was sent
    assert row["code"] == func_data["code"]
    assert row["description"] == func_data["description"]
    assert row["reliability_score"] == 95.5
    assert row["verification_status"] == "verified"

    # JSON strings must be decoded and matched
    import json
    assert json.loads(row["tags"]) == ["math", "utility"]
    assert json.loads(row["test_metrics"]) == {"passed": 3}
    assert json.loads(row["dependencies"]) == ["numpy"]
    assert json.loads(row["env_fingerprint"]) == {"python": "3.11"}
    assert json.loads(row["verification_report"]) == {"gate": "passed"}

    conn.close()


@pytest.mark.asyncio
async def test_retry_on_db_lock_decorator_failure(db_isolation):
    """Test that retry_on_db_lock raises the operational error if retries are exhausted."""
    call_count = 0

    @retry_on_db_lock(max_retries=2, base_delay=0.01)
    async def mock_fail_db_op():
        nonlocal call_count
        call_count += 1
        raise aiosqlite.OperationalError("database is locked")

    with pytest.raises(aiosqlite.OperationalError) as exc_info:
        await mock_fail_db_op()

    assert "database is locked" in str(exc_info.value)
    # 1 initial call + 2 retries = 3 calls
    assert call_count == 3
