import asyncio
import sqlite3
from pathlib import Path

import pytest

from core.config import SQLITE_DB_PATH
from core.migration import run_migrations


@pytest.fixture
def clean_db():
    from core.db import close_db_connection
    # Ensure connection is closed before test
    asyncio.run(close_db_connection())

    db_path = Path(SQLITE_DB_PATH)
    if db_path.exists():
        db_path.unlink()
    yield db_path

    # Close again after test
    asyncio.run(close_db_connection())
    if db_path.exists():
        db_path.unlink()

def test_run_migrations_creates_tables(clean_db):
    """Unit: Verifies that migrations are applied and tracking table created."""
    run_migrations()

    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()

    # Check tracking table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
    assert cursor.fetchone() is not None

    # Check function table (from 001_init.sql)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='functions'")
    assert cursor.fetchone() is not None

    # Check applied version
    cursor.execute("SELECT version FROM schema_migrations")
    assert cursor.fetchone()[0] == 1

    conn.close()

def test_migration_failure_rolls_back(clean_db):
    """Unit: Verifies that a broken migration doesn't leave the tracking table in a bad state."""
    migrations_dir = Path("src/storage/migrations")
    bad_migration = migrations_dir / "999_bad.sql"
    bad_migration.write_text("CREATE TABLE broken; -- Invalid SQL", encoding="utf-8")

    try:
        with pytest.raises(Exception):
            run_migrations()

        # Verify no tracking entry for 999
        conn = sqlite3.connect(clean_db)
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM schema_migrations WHERE version=999")
        assert cursor.fetchone() is None
        conn.close()
    finally:
        bad_migration.unlink()
