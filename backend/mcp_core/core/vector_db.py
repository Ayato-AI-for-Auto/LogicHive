import logging
import os

from mcp_core.core.config import DATA_DIR
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

logger = logging.getLogger(__name__)

# Collection Name
COLLECTION_NAME = "functions"


class VectorDB:
    """
    Manager for Qdrant Local/Embedded mode.
    Handles vector storage and search.
    """

    def __init__(self):
        db_path_env = os.environ.get("DATABASE_PATH", "")
        if db_path_env == ":memory:":
            logger.info("VectorDB: Running in-memory mode for stateless backend.")
            self.client = QdrantClient(location=":memory:")
        else:
            self.db_path = os.path.join(DATA_DIR, "qdrant_storage")
            os.makedirs(self.db_path, exist_ok=True)
            # Initialize Client in Local Mode
            self.client = QdrantClient(path=self.db_path)
        
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensures the collection exists with correct dimensions."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == COLLECTION_NAME for c in collections)

            if not exists:
                logger.info(f"VectorDB: Creating collection '{COLLECTION_NAME}'...")
                # Default dimension for FastEmbed (multilingual-mpnet-base-v2) is 768
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
                )
        except Exception as e:
            logger.error(f"VectorDB: Failed to ensure collection: {e}")

    def upsert_function(self, function_id: int, vector: list, metadata: dict):
        """Saves or updates a vector with payload."""
        try:
            from qdrant_client.http.models import PointStruct

            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[PointStruct(id=function_id, vector=vector, payload=metadata)],
            )
        except Exception as e:
            logger.error(f"VectorDB: Upsert failed: {e}")

    def search(self, vector: list, limit: int = 10) -> list:
        """Performs vector search and returns points with payload."""
        try:
            return self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as e:
            logger.error(f"VectorDB: Search failed: {e}")
            return []

    def delete(self, function_id: int):
        """Deletes a point from the collection."""
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME, points_selector=[function_id]
            )
        except Exception as e:
            logger.error(f"VectorDB: Delete failed: {e}")


_vector_db = None

def get_vector_db():
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDB()
    return _vector_db

# For backward compatibility if needed, but better to use get_vector_db()
@property
def vector_db():
    return get_vector_db()
