import logging

from core.database import get_db_connection

logger = logging.getLogger(__name__)

TABLE_NAME = "embeddings"


class VectorDB:
    def __init__(self):
        logger.info("VectorDB: Initialized using DuckDB backend.")

    def upsert_function(self, function_name: str, vector: list, metadata: dict):
        try:
            conn = get_db_connection()
            try:
                model_name = metadata.get("model_name", "unknown")
                dim = len(vector)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO embeddings (function_name, vector, model_name, dimension, encoded_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (function_name, vector, model_name, dim),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"VectorDB: Upsert failed: {e}")

    def search(self, vector: list, limit: int = 10) -> list:
        try:
            conn = get_db_connection(read_only=True)
            try:
                results = conn.execute(
                    """
                    SELECT 
                        e.function_name, 
                        f.description,
                        f.tags,
                        f.metadata,
                        list_cosine_similarity(e.vector, ?::FLOAT[]) as score
                    FROM embeddings e
                    JOIN functions f ON e.function_name = f.name
                    ORDER BY score DESC
                    LIMIT ?
                    """,
                    (vector, limit),
                ).fetchall()

                class ScoredPoint:
                    def __init__(self, id, score, payload):
                        self.id = id
                        self.score = score
                        self.payload = payload

                return [
                    ScoredPoint(
                        id=r[0],  # function_name
                        score=r[4],
                        payload={
                            "name": r[0],
                            "description": r[1],
                            "tags": r[2],
                            "metadata": r[3],
                        },
                    )
                    for r in results
                ]
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"VectorDB: Search failed: {e}")
            return []

    def delete(self, function_name: str):
        try:
            conn = get_db_connection()
            try:
                conn.execute(
                    "DELETE FROM embeddings WHERE function_name = ?", (function_name,)
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"VectorDB: Delete failed: {e}")


_vector_db = None


def get_vector_db():
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDB()
    return _vector_db
