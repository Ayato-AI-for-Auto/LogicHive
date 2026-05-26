import logging
import os
import sys

from core.config import (
    EMBEDDING_MODEL_ID,
    GEMINI_API_KEY,
    EMBEDDING_PROVIDER,
    OLLAMA_EMBEDDING_MODEL,
    FASTEMBED_MODEL,
    OLLAMA_URL,
    VECTOR_DIMENSION,
)
from core.logging_config import get_logger

# Suppress verbose third-party logging
logging.getLogger("google.genai").setLevel(logging.WARNING)

logger = get_logger(__name__)


class GeminiEmbeddingService:
    """
    Cloud Embedding Service using Google Gemini (Explicitly 768D by default).
    """

    def __init__(self):
        self.model_name = EMBEDDING_MODEL_ID
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

    def get_embedding(self, text: str, is_query: bool = False) -> list[float]:
        self._ensure_initialized()
        if not self._client:
            return [0.0] * VECTOR_DIMENSION

        try:
            result = self._client.models.embed_content(
                model=self.model_name,
                contents=text,
                config={
                    "task_type": "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT",
                    "output_dimensionality": VECTOR_DIMENSION,
                },
            )
            vector = result.embeddings[0].values
            return list(vector)
        except Exception as e:
            logger.error(f"GeminiEmbeddingService: Inference Failed - {e}")
            return [0.0] * VECTOR_DIMENSION

    def get_model_info(self) -> dict:
        return {
            "model_name": self.model_name,
            "dimension": VECTOR_DIMENSION,
            "device": "cloud",
        }


class OllamaEmbeddingService:
    """
    Local Embedding Service using Ollama embedding API.
    """

    def __init__(self):
        self.model_name = OLLAMA_EMBEDDING_MODEL
        self.url = OLLAMA_URL
        self._client = None

    def get_embedding(self, text: str, is_query: bool = False) -> list[float]:
        import httpx
        try:
            resp = httpx.post(
                f"{self.url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text,
                },
                timeout=15.0
            )
            if resp.status_code == 200:
                vector = resp.json().get("embedding", [])
                if len(vector) != VECTOR_DIMENSION:
                    logger.warning(
                        f"OllamaEmbeddingService: Vector length ({len(vector)}) mismatch with expected {VECTOR_DIMENSION}. Adjusting."
                    )
                    if len(vector) < VECTOR_DIMENSION:
                        vector = vector + [0.0] * (VECTOR_DIMENSION - len(vector))
                    else:
                        vector = vector[:VECTOR_DIMENSION]
                return vector
            else:
                logger.error(f"OllamaEmbeddingService: HTTP Error {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"OllamaEmbeddingService: Embedding generation failed: {e}")
        return [0.0] * VECTOR_DIMENSION

    def get_model_info(self) -> dict:
        return {
            "model_name": self.model_name,
            "dimension": VECTOR_DIMENSION,
            "device": "local",
        }


class FastEmbedEmbeddingService:
    """
    Local Embedding Service using fastembed library.
    """

    def __init__(self):
        self.model_name = FASTEMBED_MODEL
        self._model = None

    def _ensure_initialized(self):
        if self._model:
            return
        try:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name=self.model_name)
            logger.info(f"FastEmbedEmbeddingService: Initialized successfully with {self.model_name}")
        except ImportError:
            msg = (
                "\n" + "=" * 80 + "\n"
                "[ERROR] The 'fastembed' package is required but not installed.\n"
                "Please install it using: pip install fastembed\n"
                "Or switch EMBEDDING_PROVIDER to 'gemini' or 'ollama' in your .env.\n"
                "================================================================================\n"
            )
            print(msg, file=sys.stderr)
            logger.error("FastEmbedEmbeddingService: Missing fastembed library.")
            raise ImportError("Missing 'fastembed' package.")
        except Exception as e:
            logger.error(f"FastEmbedEmbeddingService: Initialization failed: {e}")

    def get_embedding(self, text: str, is_query: bool = False) -> list[float]:
        try:
            self._ensure_initialized()
            if not self._model:
                return [0.0] * VECTOR_DIMENSION
            embeddings = list(self._model.embed([text]))
            if embeddings:
                vector = list(embeddings[0])
                if len(vector) != VECTOR_DIMENSION:
                    if len(vector) < VECTOR_DIMENSION:
                        vector = vector + [0.0] * (VECTOR_DIMENSION - len(vector))
                    else:
                        vector = vector[:VECTOR_DIMENSION]
                return vector
        except Exception as e:
            logger.error(f"FastEmbedEmbeddingService: Embedding generation failed: {e}")
        return [0.0] * VECTOR_DIMENSION

    def get_model_info(self) -> dict:
        return {
            "model_name": self.model_name,
            "dimension": VECTOR_DIMENSION,
            "device": "local",
        }


class EmbeddingServiceDispatcher:
    """
    Dispatches embedding generation requests to the chosen provider.
    """

    def __init__(self):
        self.provider = EMBEDDING_PROVIDER
        self.gemini_service = GeminiEmbeddingService()
        self.ollama_service = OllamaEmbeddingService()
        self.fastembed_service = FastEmbedEmbeddingService()

    def get_embedding(self, text: str, is_query: bool = False) -> list[float]:
        if self.provider == "ollama":
            return self.ollama_service.get_embedding(text, is_query)
        elif self.provider == "fastembed":
            return self.fastembed_service.get_embedding(text, is_query)
        else:
            return self.gemini_service.get_embedding(text, is_query)

    def get_model_info(self) -> dict:
        if self.provider == "ollama":
            return self.ollama_service.get_model_info()
        elif self.provider == "fastembed":
            return self.fastembed_service.get_model_info()
        else:
            return self.gemini_service.get_model_info()


# Dispatcher Singleton Instance
embedding_service = EmbeddingServiceDispatcher()
