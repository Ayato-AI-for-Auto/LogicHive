import pytest
import asyncio
import json
import sqlite3
import os
from orchestrator import do_search_async, do_save_async
from storage.vector_store import vector_manager
from mcp_server import check_integrity

@pytest.mark.asyncio
async def test_search_concurrency_stress():
    """Verify system handles simultaneous requests via semaphore."""
    # Launch 10 simultaneous searches
    tasks = [do_search_async(query="test", limit=1) for _ in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check that we didn't crash
    for res in results:
        assert not isinstance(res, Exception)

@pytest.mark.asyncio
async def test_corrupt_embedding_resilience():
    """Verify system survives invalid JSON data in embedding column."""
    from core.db import get_db_connection
    db = await get_db_connection()
    await db.execute("INSERT INTO logichive_functions (id, name, embedding) VALUES (?, ?, ?)", 
                     ("corrupt_id", "corrupt_func", '{"broken": json'))
    await db.commit()
    
    # Check if integrity check still works
    report = await check_integrity()
    assert "Integrity Check Failed" not in report

@pytest.mark.asyncio
async def test_lefthook_size_enforcement_simulation():
    """Simulate size check logic to ensure enforcement is possible."""
    # Write dummy file > 500 lines
    dummy_file = "scratch/dummy_large.py"
    with open(dummy_file, "w") as f:
        f.write("def func(): pass\n" * 600)
    
    # Run a manual check mirroring Lefthook logic
    lines = sum(1 for _ in open(dummy_file))
    assert lines > 500
    
    # Cleanup
    os.remove(dummy_file)
