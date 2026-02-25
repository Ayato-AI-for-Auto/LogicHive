import json
import logging
import os
import sys

# Setup paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

from mcp_core.core.database import get_db_connection  # noqa: E402
from mcp_core.core.vector_db import vector_db  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Migrates existing embeddings from DuckDB to Qdrant."""
    logger.info("Starting migration from DuckDB to Qdrant...")

    conn = get_db_connection(read_only=True)
    try:
        # Fetch all functions with their current embeddings
        sql = """
            SELECT f.id, f.name, f.description, f.tags, f.status, e.vector,
                   COALESCE(CAST(json_extract(f.metadata, '$.quality_score') AS INTEGER), 50) as qs
            FROM functions f
            JOIN embeddings e ON f.id = e.function_id
            WHERE f.status != 'deleted'
        """
        rows = conn.execute(sql).fetchall()

        if not rows:
            logger.info("No data found to migrate.", flush=True)
            return

        logger.info(f"Found {len(rows)} functions to migrate.", flush=True)

        for r in rows:
            fid, name, desc, tags_raw, status, vector_raw, qs = r
            tags = json.loads(tags_raw) if tags_raw else []

            # DuckDB returns vector as list or array-like
            vector = vector_raw

            payload = {
                "name": name,
                "description": desc,
                "tags": tags,
                "status": status,
                "quality_score": qs,
            }

            logger.info(f"Migrating function: {name} (ID: {fid})")
            vector_db.upsert_function(fid, vector, payload)

        logger.info("Migration completed successfully.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
