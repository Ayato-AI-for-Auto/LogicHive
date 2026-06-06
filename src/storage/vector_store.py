"""
LogicHive Vector Store: ChromaDB による永続化とセマンティック検索を提供します。
ADR-0018 に基づき、Faiss からの移行版。
"""

import asyncio
import json
from typing import Any

import chromadb

from core.config import (
    CHROMA_DB_DIR,
    VECTOR_DIMENSION,
    get_active_embedding_model_name,
)
from core.db import get_db_connection
from core.exceptions import StorageError
from core.logging_config import get_logger

logger = get_logger(__name__)


class VectorIndexManager:
    """ChromaDB を使用してベクトルインデックスとメタデータを管理します。"""

    def __init__(self):
        self.client: Any = None
        self.collection: Any = None
        self._lock = asyncio.Lock()
        self._initialized = False

    def _get_collection_name(self) -> str:
        """現在のEmbeddingモデル名から安全なコレクション名を生成します。"""
        model_name = get_active_embedding_model_name()
        # ChromaDB の制限: 3-63文字, 英数字/_- のみ, 開始終了は英数字
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in model_name)
        # 先頭が記号の場合はプレフィックスを付ける
        if not safe_name[0].isalnum():
            safe_name = f"lh_{safe_name}"
        # 長さ制限
        safe_name = safe_name[:63].strip("_")
        if len(safe_name) < 3:
            safe_name = f"logichive_{safe_name}"
        return safe_name

    async def ensure_initialized(self, db_rows: list[dict[str, Any]]):
        """クライアントとコレクションを初期化し、必要であればDBと同期します。"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
                # SQLite へのコネクション確立前に ChromaDB が立ち上がるようにする
                self.client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

                collection_name = self._get_collection_name()
                # Cosine 距離を使用するように設定
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )

                # 同期チェック (簡易的に件数で比較)
                current_count = self.collection.count()
                db_valid_rows = [r for r in db_rows if r.get("embedding")]
                expected_count = len(db_valid_rows)

                if current_count < expected_count:
                    logger.info(f"ChromaDB: Syncing {expected_count - current_count} missing vectors...")
                    ids, embeddings, metadatas = [], [], []

                    for row in db_valid_rows:
                        emb = row["embedding"]
                        if isinstance(emb, str):
                            try:
                                emb = json.loads(emb)
                            except json.JSONDecodeError:
                                continue

                        if emb and len(emb) == VECTOR_DIMENSION:
                            p, n = row.get("project", "default"), row["name"]
                            full_key = f"{p}:{n}"
                            ids.append(full_key)
                            embeddings.append(emb)
                            metadatas.append({"project": p, "name": n})

                    if ids:
                        # 大量データの場合はバッチ分割が必要だが、MVPでは一括
                        self.collection.upsert(
                            ids=ids,
                            embeddings=embeddings,
                            metadatas=metadatas
                        )

                self._initialized = True
                logger.info(f"ChromaDB: Initialized collection '{collection_name}' (Count: {self.collection.count()})")
            except Exception as e:
                logger.error(f"ChromaDB: Initialization failed: {e}", exc_info=True)
                raise StorageError(f"Vector Store Initialization failed: {e}") from e

    async def upsert_vector(
        self, name: str, embedding: list[float], metadata: dict[str, Any] = None, project: str = "default"
    ):
        """単一のベクトルを更新または追加します。"""
        if not self._initialized:
            # 最小限の初期化を試みる
            try:
                await self.ensure_initialized([])
            except Exception:
                return

        async with self._lock:
            full_key = f"{project}:{name}"
            if len(embedding) != VECTOR_DIMENSION:
                logger.warning(f"ChromaDB: Dimension mismatch for '{full_key}'.")
                return

            try:
                meta = metadata or {}
                meta.update({"project": project, "name": name})
                self.collection.upsert(
                    ids=[full_key],
                    embeddings=[embedding],
                    metadatas=[meta]
                )
                logger.debug(f"ChromaDB: Upserted '{full_key}'")
            except Exception as e:
                logger.error(f"ChromaDB: Upsert failed: {e}")

    async def remove_vector(self, name: str, project: str = "default"):
        """ベクトルを削除します。"""
        if not self._initialized:
            return
        async with self._lock:
            full_key = f"{project}:{name}"
            try:
                self.collection.delete(ids=[full_key])
                logger.info(f"ChromaDB: Deleted '{full_key}'")
            except Exception as e:
                logger.error(f"ChromaDB: Delete failed: {e}")

    async def rebuild_index(self):
        """現在のコレクションをリセットし、SQLite から全件再構築します。"""
        async with self._lock:
            try:
                collection_name = self._get_collection_name()
                logger.info(f"ChromaDB: Rebuilding collection '{collection_name}'...")

                if not self.client:
                    self.client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

                try:
                    self.client.delete_collection(name=collection_name)
                except Exception:
                    pass

                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )

                db = await get_db_connection()
                async with db.execute(
                    "SELECT project, name, embedding FROM logichive_functions WHERE embedding IS NOT NULL AND embedding != 'null'"
                ) as cursor:
                    rows = await cursor.fetchall()

                ids, embeddings, metadatas = [], [], []
                for row in rows:
                    try:
                        emb = json.loads(row["embedding"]) if isinstance(row["embedding"], str) else row["embedding"]
                        if emb and len(emb) == VECTOR_DIMENSION:
                            p, n = row["project"], row["name"]
                            ids.append(f"{p}:{n}")
                            embeddings.append(emb)
                            metadatas.append({"project": p, "name": n})
                    except Exception:
                        continue

                if ids:
                    self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

                self._initialized = True
                logger.info(f"ChromaDB: Rebuild complete. (Count: {self.collection.count()})")
            except Exception as e:
                logger.error(f"ChromaDB: Rebuild failed: {e}")
                raise StorageError(f"Vector Store Rebuild failed: {e}") from e

    async def search(
        self, query_emb: list[float], limit: int = 5, project: str | None = None
    ) -> list[dict[str, Any]]:
        """類似ベクトルを検索します。"""
        if not self._initialized:
            return []

        try:
            where = {"project": project} if project else None

            results = self.collection.query(
                query_embeddings=[query_emb],
                n_results=limit,
                where=where
            )

            output = []
            if results["ids"] and results["ids"][0]:
                for i, full_key in enumerate(results["ids"][0]):
                    # ChromaDB の distance (cosine distance = 1 - cosine similarity) を
                    # 以前のコードと互換性のある similarity に変換
                    dist = results["distances"][0][i] if results["distances"] else 0.5
                    output.append({
                        "name": results["metadatas"][0][i]["name"],
                        "project": results["metadatas"][0][i]["project"],
                        "similarity": 1.0 - dist
                    })
            return output
        except Exception as e:
            logger.error(f"ChromaDB: Search failed: {e}")
            return []

    async def check_health(self) -> dict[str, Any]:
        """コンポーネントの状態を確認します。"""
        try:
            if not self._initialized:
                return {"status": "Warning", "message": "Vector store not initialized."}

            count = self.collection.count()
            return {
                "status": "Healthy",
                "message": f"ChromaDB OK. Collection '{self._get_collection_name()}' count: {count}",
                "details": {"total": count}
            }
        except Exception as e:
            return {"status": "Error", "message": str(e)}


# Singleton
vector_manager = VectorIndexManager()
