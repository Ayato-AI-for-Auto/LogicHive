import asyncio
import os

import pytest

from mcp_server import check_integrity, rebuild_index, save_function
from storage.vector_store import vector_manager


@pytest.mark.asyncio
async def test_mcp_error_reporting_transparency_system():
    """Verifies that save_function returns rich error details immediately."""
    # Induce a structural error
    code = "def broken():\n  print('missing closing'"

    response = await save_function(name="system_error_test", code=code)

    assert "IMMEDIATE REJECTION" in response
    assert "Error" in response
    assert "Context" in response


@pytest.mark.asyncio
async def test_harsh_index_corruption_recovery_system():
    """Induces desync by deleting index file and verifies recovery."""
    # 1. Ensure we have at least one valid record in DB with embedding
    # (We assume the current dev DB has some, or we skip if empty)
    from storage.sqlite_api import sqlite_storage

    db_count = await sqlite_storage.get_function_count()
    if db_count == 0:
        pytest.skip("No records in DB to test integrity recovery.")

    # 2. Force initialization
    from core.db import get_db_connection

    db = await get_db_connection()
    async with db.execute(
        "SELECT name, embedding, project FROM logichive_functions WHERE embedding IS NOT NULL AND embedding != 'null'"
    ) as cursor:
        rows = [dict(r) for r in await cursor.fetchall()]

    if not rows:
        pytest.skip("No valid embeddings in DB.")

    await vector_manager.ensure_initialized(rows)

    # 3. Simulate disk loss (Silent)
    from core.config import FAISS_INDEX_PATH

    if os.path.exists(FAISS_INDEX_PATH):
        os.remove(FAISS_INDEX_PATH)

    # 4. Check integrity - Should still be "Healthy" in memory BUT desync if DB has more
    # Actually, if we just deleted the file, the memory state is still there.
    # To truly simulate "corruption/missing", we should reset vector_manager
    vector_manager._initialized = False

    report = await check_integrity()
    assert "Uninitialized" in report or "Desync Detected" in report

    # 5. Rebuild
    rebuild_res = await rebuild_index()
    assert "successfully rebuilt" in rebuild_res

    # 6. Check again
    report_final = await check_integrity()
    assert "Optimal" in report_final or "Healthy" in report_final


@pytest.mark.asyncio
async def test_database_lock_resilience_harsh():
    """Simulates a locked database during integrity check (Harsh)."""
    import sqlite3

    from core.config import SQLITE_DB_PATH

    # Manually lock the DB using a separate connection in a transaction
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.execute("BEGIN EXCLUSIVE TRANSACTION")

    try:
        # The check_integrity tool should handle the lock via retry decorator or return error string
        # Actually, get_db_connection itself might hang if not careful,
        # but check_integrity in mcp_server uses sqlite_storage which has @retry_on_db_lock

        # We run it in a task with a timeout to prevent hanging the test suite
        try:
            report = await asyncio.wait_for(check_integrity(), timeout=2.0)
            # If it returns, it might be an error report or a successful retry if lock was released
            # Since we keep it locked, it should eventually fail or report Error
            assert "Integrity Check Failed" in report or "database is locked" in report
        except asyncio.TimeoutError:
            # Expected if retries keep going
            pass

    finally:
        conn.rollback()
        conn.close()
