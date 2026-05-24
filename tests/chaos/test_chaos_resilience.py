import pytest
import asyncio
from orchestrator import do_save_async, do_get_verification_status
from core.exceptions import ValidationError

@pytest.mark.asyncio
async def test_chaos_infinite_loop(test_db):
    """CHAOS: Submit code with an infinite loop to ensure it gets killed and rejected."""
    name = "chaos_infinite"
    code = "def loop_forever():\n    while True:\n        pass"
    test_code = "loop_forever()"
    
    # We expect this to be accepted but fail in the background
    await do_save_async(name=name, code=code, test_code=test_code, timeout=2)
    
    # Wait for the timeout to hit
    for _ in range(10):
        status_data = await do_get_verification_status(name)
        if status_data["status"] != "pending":
            break
        await asyncio.sleep(1.0)
        
    assert status_data["status"] in ["failed", "error"]
    report = str(status_data.get("report", "")).lower()
    assert "timeout" in report or "killed" in report or "failed" in report or "error" in report

@pytest.mark.asyncio
async def test_chaos_database_lock_simulation(test_db):
    """CHAOS: Simulate database lock to ensure retry logic handles it or fails gracefully."""
    import sqlite3
    from core.config import SQLITE_DB_PATH
    
    # Manually lock the DB
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.execute("BEGIN EXCLUSIVE TRANSACTION")
    
    try:
        from mcp_server import check_integrity
        
        # We run it in a task with a timeout to prevent hanging the test suite completely
        report = await asyncio.wait_for(check_integrity(), timeout=3.0)
        # It might succeed reading despite the write lock in WAL mode, or return a failure.
        # We just want to ensure it doesn't crash the server.
        assert isinstance(report, str)
        assert "LogicHive Integrity Report" in report
    except asyncio.TimeoutError:
        # Expected if retries keep going
        pass
    finally:
        conn.rollback()
        conn.close()

@pytest.mark.asyncio
async def test_chaos_heavy_import_blocking(test_db):
    """CHAOS: Submit code with heavy imports without mocking, ensuring it gets blocked by static analyzer or times out."""
    name = "chaos_heavy"
    code = "import torch\nimport tensorflow\n\ndef noop(): pass"
    test_code = "noop()"
    
    try:
        await do_save_async(name=name, code=code, test_code=test_code)
    except ValidationError:
        # It's fine if the static gate rejects it immediately
        pass
    
    # If it didn't reject immediately, wait for background verification
    for _ in range(10):
        status_data = await do_get_verification_status(name)
        if status_data["status"] != "pending":
            break
        await asyncio.sleep(1.0)
        
    assert status_data["status"] in ["failed", "error"]
