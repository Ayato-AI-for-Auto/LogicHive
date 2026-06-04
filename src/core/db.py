import asyncio
from functools import wraps

import aiosqlite

from core.logging_config import get_logger

logger = get_logger(__name__)

# Single global connection to avoid "threads can only be started once" on Windows
_global_db = None
_db_lock = asyncio.Lock()
_creator_loop = None


async def get_db_connection() -> aiosqlite.Connection:
    """
    Includes loop-affinity check for Windows stability.
    Ensures tables are created on the first connection.
    """
    import time

    start_time = time.perf_counter()
    logger.info("[TRACE] SQLite: Requesting DB connection...")      
    global _global_db, _creator_loop
    current_loop = asyncio.get_running_loop()

    async with _db_lock:
        # If loop changed, we MUST re-initialize because aiosqlite threads
        # are tied to the creator's event loop environment.
        if _global_db is not None and _creator_loop is not current_loop:
            logger.warning("Loop affinity change detected. Re-initializing DB.")
            # We don't await close on the old connection because it might be tied
            # to a dead loop, which causes a hang. We orphan it.    
            _global_db = None

        if _global_db is None:
            from core.config import get_sqlite_db_path
            _global_db = await aiosqlite.connect(get_sqlite_db_path())
            _global_db.row_factory = aiosqlite.Row
            _creator_loop = current_loop

            await _global_db.execute("PRAGMA journal_mode=WAL;")    
            await _global_db.execute("PRAGMA synchronous=NORMAL;")  
            await _global_db.execute("PRAGMA busy_timeout=5000;")   

            # --- Initialize Database Schema ---
            await _global_db.execute("""
            CREATE TABLE IF NOT EXISTS logichive_functions (
                id TEXT PRIMARY KEY,
                project TEXT DEFAULT 'default',
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                reliability_score REAL DEFAULT 1.0,
                test_metrics TEXT,
                embedding TEXT,
                language TEXT DEFAULT 'python',
                call_count INTEGER DEFAULT 0,
                code_hash TEXT,
                version INTEGER DEFAULT 1,
                dependencies TEXT,
                test_code TEXT,
                env_fingerprint TEXT,
                verification_status TEXT DEFAULT 'pending',
                verification_report TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project, name)
            );
            """)
            await _global_db.execute("""
            CREATE TABLE IF NOT EXISTS logichive_function_history (
                history_id TEXT PRIMARY KEY,
                function_id TEXT NOT NULL,
                project TEXT DEFAULT 'default',
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                language TEXT,
                version INTEGER NOT NULL,
                code_hash TEXT,
                dependencies TEXT,
                test_code TEXT,
                env_fingerprint TEXT,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            await _global_db.execute("CREATE INDEX IF NOT EXISTS idx_func_project_name ON logichive_functions(project, name);")
            await _global_db.execute("CREATE INDEX IF NOT EXISTS idx_func_hash ON logichive_functions(code_hash);")
            await _global_db.execute("CREATE INDEX IF NOT EXISTS idx_hist_name ON logichive_function_history(name);")
            await _global_db.commit()

        duration = time.perf_counter() - start_time
        logger.info(f"[TRACE] SQLite: DB connection acquired in {duration:.4f}s")
        return _global_db


async def close_db_connection():
    """Explicitly closes the global connection."""
    global _global_db, _creator_loop
    async with _db_lock:
        if _global_db is not None:
            try:
                # We only try to close if we are in the same loop
                if _creator_loop is asyncio.get_running_loop():
                    await _global_db.close()
            except Exception as e:
                logger.exception(f"Error closing shared DB: {e}")
            finally:
                _global_db = None
                _creator_loop = None


async def init_connection_pragmas(db: aiosqlite.Connection):
    """Initializes pragmas for a new connection. (Currently handled in get_db_connection)"""
    logger.info(
        "[TRACE] SQLite: Initializing connection pragmas (noop - moved to get_db_connection)"
    )


def retry_on_db_lock(max_retries: int = 5, base_delay: float = 0.1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except aiosqlite.OperationalError as e:
                    if "database is locked" in str(e).lower() and retries < max_retries:
                        delay = base_delay * (2**retries)
                        logger.warning(f"DB Locked. Retry {retries + 1}")
                        await asyncio.sleep(delay)
                        retries += 1
                    else:
                        logger.exception("DB operation failed after retries")
                        raise

        return wrapper

    return decorator
