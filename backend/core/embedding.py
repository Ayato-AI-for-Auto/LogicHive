import logging
from typing import List

from core.config import (
    GEMINI_API_KEY,
    MODEL_TYPE,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
)

# Suppress verbose third-party logging
# google-genai logs can also be verbose
logging.getLogger("google.genai").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class GeminiEmbeddingService:
    """
    Cloud Embedding Service using Google Gemini (1536D).
    """

    def __init__(self):
        self.model_name = (
            "models/text-embedding-004"  # Latest recommended for embeddings
        )
        self._api_key = GEMINI_API_KEY
        self._client = None

    def _ensure_initialized(self):
        if self._client:
            return

        if not self._api_key:
            logger.error("GeminiEmbeddingService: API Key is missing. Check settings.")
            return

        try:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
            logger.info("GeminiEmbeddingService: Initialized successfully.")
        except Exception as e:
            logger.error(f"GeminiEmbeddingService: Initialization Failed: {e}")

    def get_embedding(self, text: str, is_query: bool = False) -> List[float]:
        self._ensure_initialized()
        if not self._client:
            return [0.0] * 1536

        try:
            # text-embedding-004 supports 1536D by default
            result = self._client.models.embed_content(
                model=self.model_name,
                contents=text,
                config={
                    "task_type": "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
                },
            )
            # Result contains 'embeddings', a list of values
            vector = result.embeddings[0].values
            return list(vector)

        except Exception as e:
            logger.error(f"GeminiEmbeddingService: Inference Failed - {e}")
            return [0.0] * 1536

    def get_model_info(self) -> dict:
        return {
            "model_name": self.model_name,
            "dimension": 1536,
            "device": "cloud",
        }


class OllamaEmbeddingService:
    """
    Local/Self-hosted Embedding Service using Ollama.
    """

    def __init__(self):
        self.model_name = OLLAMA_EMBED_MODEL
        self.base_url = OLLAMA_BASE_URL

    def get_embedding(self, text: str, is_query: bool = False) -> List[float]:
        try:
            import httpx

            resp = httpx.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text},
                timeout=30.0,
            )
            resp.raise_for_status()
            vector = resp.json()["embedding"]
            return list(vector)
        except Exception as e:
            logger.error(f"OllamaEmbeddingService: Inference Failed - {e}")
            return [0.0] * 1024

    def get_model_info(self) -> dict:
        return {
            "model_name": self.model_name,
            "dimension": 1024,  # mxbai-embed-large default
            "device": "ollama",
        }


# Singleton Instance
if MODEL_TYPE == "gemini":
    embedding_service = GeminiEmbeddingService()
elif MODEL_TYPE == "ollama":
    embedding_service = OllamaEmbeddingService()
else:
    # Default fallback to zero vector service if nothing else matches
    logger.warning(
        f"No valid embedding service for MODEL_TYPE '{MODEL_TYPE}'. Using Gemini as primary."
    )
    embedding_service = GeminiEmbeddingService()
