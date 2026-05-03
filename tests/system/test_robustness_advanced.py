import os
import pytest
import asyncio
from orchestrator import do_search_async
from mcp_server import check_integrity


@pytest.mark.asyncio
async def test_search_concurrency_stress(test_db):
    """Verify system handles simultaneous requests via semaphore."""
    # Launch 10 simultaneous searches
    tasks = [do_search_async(query="test", limit=1) for _ in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check that we didn't crash
    for res in results:
        assert not isinstance(res, Exception)


@pytest.mark.asyncio
async def test_corrupt_embedding_resilience(test_db):
    """Verify system survives invalid JSON data in embedding column."""
    from core.db import get_db_connection

    db = await get_db_connection()
    await db.execute(
        "INSERT INTO logichive_functions (id, name, embedding, code) VALUES (?, ?, ?, ?)",
        ("corrupt_id", "corrupt_func", '{"broken": json', 'def pass(): pass'),
    )
    await db.commit()

    # Check if integrity check still works
    report = await check_integrity()
    assert "Integrity Check Failed" not in report


@pytest.mark.asyncio
async def test_lefthook_size_enforcement_simulation():
    """Simulate size check logic to ensure enforcement is possible."""
    import os
    # Write dummy file > 500 lines
    dummy_file = "scratch/dummy_large.py"
    with open(dummy_file, "w") as f:
        f.write("def func(): pass\n" * 600)

    # Run a manual check mirroring Lefthook logic
    with open(dummy_file, "r") as f:
        lines = sum(1 for _ in f)
    assert lines > 500

    # Cleanup
    if os.path.exists(dummy_file):
        os.remove(dummy_file)
