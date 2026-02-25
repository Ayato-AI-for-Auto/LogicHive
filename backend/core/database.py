import json
import logging
import os
import time

import duckdb
from core import config
from core.embedding import embedding_service

try:
    import msvcrt
    _HAS_MSVCRT = True
except ImportError:
    _HAS_MSVCRT = False

import threading

logger = logging.getLogger(__name__)

LOCK_PATH = config.DATA_DIR / "functions.duckdb.lock"
_inner_lock = threading.Lock()


class DBWriteLock:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self._fp = None

    def __enter__(self):
        if not _inner_lock.acquire(timeout=self.timeout):
            raise TimeoutError("Could not acquire internal thread lock.")

        if not _HAS_MSVCRT:
            return self

        try:
            LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._fp = open(LOCK_PATH, "a")
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    msvcrt.locking(self._fp.fileno(), msvcrt.LK_NBLCK, 1)
                    return self
                except OSError:
                    if time.monotonic() > deadline:
                        raise TimeoutError("Could not acquire database lock.")
                    time.sleep(0.1)
        except Exception:
            _inner_lock.release()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self._fp:
                try:
                    msvcrt.locking(self._fp.fileno(), msvcrt.LK_UNLCK, 1)
                except Exception:
                    pass
                finally:
                    self._fp.close()
                    self._fp = None
        finally:
            _inner_lock.release()


def get_db_connection(read_only=False):
    max_retries = 10
    retry_delay = 0.2
    last_err = None
    for attempt in range(max_retries):
        try:
            db_path = str(config.DB_PATH)
            if db_path != ":memory:":
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn = duckdb.connect(db_path, read_only=read_only)
            return conn
        except (duckdb.IOException, duckdb.Error) as e:
            last_err = e
            msg = str(e).lower()
            if any(x in msg for x in ["access", "in use", "locked", "open"]):
                time.sleep(retry_delay * (1.5**attempt))
                continue
            raise
    raise last_err


def init_db():
    with DBWriteLock():
        conn = get_db_connection()
        try:
            conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_emb_id START 1")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS functions (
                    name VARCHAR PRIMARY KEY,
                    code VARCHAR,
                    description VARCHAR,
                    tags VARCHAR,
                    metadata VARCHAR,
                    status VARCHAR DEFAULT 'active',
                    test_cases VARCHAR,
                    call_count INTEGER DEFAULT 0,
                    last_called_at VARCHAR,
                    created_at VARCHAR,
                    updated_at VARCHAR
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY DEFAULT nextval('seq_emb_id'),
                    function_name VARCHAR,
                    vector FLOAT[],
                    model_name VARCHAR,
                    dimension INTEGER,
                    encoded_at VARCHAR
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key VARCHAR PRIMARY KEY,
                    value VARCHAR
                )
            """)
            
            # Simple migration for embeddings if needed
            columns_res = conn.execute("DESCRIBE embeddings").fetchall()
            cols = [r[0] for r in columns_res]
            if "function_id" in cols and "function_name" not in cols:
                conn.execute("ALTER TABLE embeddings ADD COLUMN function_name VARCHAR")
            
            _check_model_version_internal(conn)
            recover_embeddings_internal(conn)
        finally:
            conn.close()


def recover_embeddings_internal(conn):
    try:
        current_model = embedding_service.model_name
        expected_dim = embedding_service.get_model_info()["dimension"]
        rows = conn.execute("""
            SELECT f.name, f.description, f.tags, f.metadata, f.code
            FROM functions f
            LEFT JOIN embeddings e ON f.name = e.function_name
            WHERE e.model_name != ? OR e.dimension != ? OR e.function_name IS NULL
        """, (current_model, expected_dim)).fetchall()
        for row in rows:
            name, desc, tags_j, meta_j, code = row
            tags = json.loads(tags_j) if tags_j else []
            meta = json.loads(meta_j) if meta_j else {}
            deps = meta.get("dependencies", [])
            text = f"Name: {name}\nDesc: {desc}\nTags: {tags}\nDeps: {deps}\nCode:\n{code[:500]}"
            emb = embedding_service.get_embedding(text)
            conn.execute("""
                INSERT OR REPLACE INTO embeddings (function_name, vector, model_name, dimension, encoded_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (name, emb, current_model, len(emb)))
        conn.commit()
    except Exception as e:
        logger.error(f"Recovery failed: {e}")


def _check_model_version_internal(conn):
    try:
        row = conn.execute("SELECT value FROM config WHERE key = 'embedding_model'").fetchone()
        current = embedding_service.model_name
        if not row:
            conn.execute("INSERT INTO config VALUES ('embedding_model', ?)", (current,))
        elif row[0] != current:
            conn.execute("UPDATE config SET value = ? WHERE key = 'embedding_model'", (current,))
        conn.commit()
    except Exception as e:
        logger.error(f"Model version check failed: {e}")

def recover_embeddings():
    with DBWriteLock():
        conn = get_db_connection()
        try: recover_embeddings_internal(conn)
        finally: conn.close()
