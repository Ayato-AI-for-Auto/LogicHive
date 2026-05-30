import sqlite3
from pathlib import Path

from core.config import SQLITE_DB_PATH
from core.logging_config import get_logger

logger = get_logger(__name__)


def run_migrations():
    """
    Applies pending SQL migrations from src/storage/migrations/
    Version tracking is done via a dedicated 'schema_migrations' table.
    """
    db_path = Path(SQLITE_DB_PATH)
    migrations_dir = Path(__file__).parent.parent / "storage" / "migrations"

    conn = sqlite3.connect(db_path)
    try:
        # 1. Ensure migration tracking table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Get applied versions
        applied = {
            row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
        }

        # 3. Find pending migration files (e.g., 001_init.sql)
        migration_files = sorted(list(migrations_dir.glob("*.sql")))

        for file_path in migration_files:
            # Extract version from filename (e.g., 001 from 001_init.sql)
            version = int(file_path.name.split("_")[0])

            if version not in applied:
                logger.info(f"Applying migration: {file_path.name}")
                with open(file_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())

                conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
                conn.commit()
                logger.info(f"Migration {file_path.name} applied successfully.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
