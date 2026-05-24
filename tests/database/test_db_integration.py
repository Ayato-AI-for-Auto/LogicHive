import asyncio

import pytest

from core.db import close_db_connection, get_db_connection


@pytest.mark.asyncio
async def test_db_connection_and_io():
    """Integration: Tests connection, auto-migration, and data I/O."""
    # Ensure migration runs
    conn = await get_db_connection()

    # Test Data I/O
    await conn.execute("INSERT INTO config (key, value) VALUES (?, ?)", ("test_key", "test_val"))
    await conn.commit()

    res = await conn.execute("SELECT value FROM config WHERE key = ?", ("test_key",))
    row = await res.fetchone()
    assert row[0] == "test_val"

    await close_db_connection()

@pytest.mark.asyncio
async def test_concurrent_db_access():
    """Integration: Tests concurrent access handling via pool/locks."""
    async def task(i):
        conn = await get_db_connection()
        # Use unique key per task
        await conn.execute("INSERT INTO config (key, value) VALUES (?, ?)", (f"concurrent_{i}", "ok"))
        await conn.commit()
        return True

    results = await asyncio.gather(task(1), task(2), task(3))
    assert all(results)

    await close_db_connection()
