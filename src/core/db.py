import asyncio
from functools import wraps
from typing import Optional

import aiosqlite

from core.logging_config import get_logger

logger = get_logger(__name__)

# Connection pool configuration
_POOL_SIZE = 3
_pool: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue(maxsize=_POOL_SIZE)
_pool_initialized = False
_pool_lock = asyncio.Lock()
_creator_loop: Optional[asyncio.AbstractEventLoop] = None


async def _create_connection() -> aiosqlite.Connection:
    """Create a new database connection with proper pragmas and schema."""
    from core.config import get_sqlite_db_path

    db = await aiosqlite.connect(get_sqlite_db_path())
    db.row_factory = aiosqlite.Row

    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA synchronous=NORMAL;")
    await db.execute("PRAGMA busy_timeout=5000;")

    # Initialize schema
    await db.execute("""
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
    await db.execute("""
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
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_func_project_name ON logichive_functions(project, name);"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_func_hash ON logichive_functions(code_hash);"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_hist_name ON logichive_function_history(name);"
    )
    await db.commit()

    return db


async def _initialize_pool() -> None:
    """Initialize the connection pool with _POOL_SIZE connections."""
    global _pool_initialized, _creator_loop

    current_loop = asyncio.get_running_loop()

    async with _pool_lock:
        if _pool_initialized and _creator_loop is current_loop:
            return

        # If loop changed, drain old pool (best effort)
        if _pool_initialized and _creator_loop is not current_loop:
            logger.warning("Event loop changed, re-initializing connection pool")
            while not _pool.empty():
                try:
                    old_conn = _pool.get_nowait()
                    await old_conn.close()
                except Exception:
                    pass

        _creator_loop = current_loop

        for _ in range(_POOL_SIZE):
            conn = await _create_connection()
            _pool.put_nowait(conn)

        _pool_initialized = True
        logger.info(f"Database connection pool initialized with {_POOL_SIZE} connections")


class _PoolConnection:
    """Context manager for pooled database connection."""

    def __init__(self):
        self.conn: Optional[aiosqlite.Connection] = None

    async def __aenter__(self) -> aiosqlite.Connection:
        await _initialize_pool()
        self.conn = await _pool.get()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.conn is not None:
            try:
                await _pool.put(self.conn)
            except Exception as e:
                logger.warning(f"Failed to release connection to pool: {e}")
                try:
                    await self.conn.close()
                except Exception:
                    pass
            self.conn = None


async def get_db_connection() -> aiosqlite.Connection:
    """
    Get a database connection from the pool.
    Use as async context manager: async with get_db_connection() as db:
    Or call release_db_connection() when done.
    """
    await _initialize_pool()
    return await _pool.get()


async def release_db_connection(conn: aiosqlite.Connection) -> None:
    """Release a connection back to the pool."""
    try:
        await _pool.put(conn)
    except Exception as e:
        logger.warning(f"Failed to release connection to pool: {e}")
        try:
            await conn.close()
        except Exception:
            pass


def db_connection():
    """Return an async context manager for a pooled database connection."""
    return _PoolConnection()


async def close_db_connection() -> None:
    """Close all connections in the pool."""
    global _pool_initialized, _creator_loop

    async with _pool_lock:
        while not _pool.empty():
            try:
                conn = _pool.get_nowait()
                await conn.close()
            except Exception as e:
                logger.debug(f"Error closing pooled connection: {e}")

        _pool_initialized = False
        _creator_loop = None
        logger.info("Database connection pool closed")


async def init_connection_pragmas(db: aiosqlite.Connection) -> None:
    """Initializes pragmas for a new connection. (Handled in _create_connection)"""
    logger.debug("[TRACE] SQLite: init_connection_pragmas called (noop)")


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