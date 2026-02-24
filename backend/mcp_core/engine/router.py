import logging
from typing import Dict, List, Optional

from mcp_core.core.config import (
    GEMINI_API_KEY,
    MODEL_TYPE,
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
)

logger = logging.getLogger(__name__)


class IntelligenceRouter:
    """
    Reranks search results to find the best match for a natural language intent.
    Supports Gemini (Cloud) and Qwen (Local via llama-cpp).
    """

    def __init__(self):
        self.mode = MODEL_TYPE  # "gemini" or "ollama"

    def _query_gemini(self, prompt: str) -> str:
        """Calls Gemini API to evaluate candidates."""
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",  # Use a fast model for reranking
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Router: Gemini evaluation failed: {e}")
            return "NONE"

    def _query_ollama(self, prompt: str) -> str:
        """Calls Ollama API to evaluate candidates."""
        try:
            import httpx

            resp = httpx.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_CHAT_MODEL,
                    "prompt": f"{prompt}\n\nDecision (Output only the function name):",
                    "stream": False,
                    "options": {"temperature": 0.0},
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()["response"].strip()
        except Exception as e:
            logger.error(f"Router: Ollama evaluation failed: {e}")
            return "NONE"

    def evaluate_matching(self, query: str, candidates: List[Dict]) -> Optional[str]:
        """
        Evaluates which candidate best matches the user intent.
        Returns the 'name' of the best function, or None if no good match is found.
        """
        if not candidates:
            return None

        # Build prompt for LLM
        candidate_info = ""
        for i, c in enumerate(candidates):
            candidate_info += f"[{i + 1}] Name: {c['name']}\nDescription: {c['description']}\nTags: {c['tags']}\n\n"

        prompt = (
            f"You are a routing agent for a function store.\n"
            f'User Query: "{query}"\n\n'
            f"Candidates:\n{candidate_info}"
            f"Instruction: Based on the User Query, select the one most relevant function from the candidates. "
            f"If none of them match, respond with 'NONE'. Otherwise, respond ONLY with the exact function name."
        )

        decision = "NONE"
        if self.mode == "gemini" and GEMINI_API_KEY:
            decision = self._query_gemini(prompt)
        elif self.mode == "ollama":
            decision = self._query_ollama(prompt)
        else:
            logger.warning(
                f"Router: Unrecognized mode '{self.mode}' or missing API key. Falling back to keyword search."
            )

        # Cleanup decision (sometimes LLMs add extra text)
        decision = decision.split("\n")[0].strip().replace("'", "").replace('"', "")

        valid_names = {c["name"] for c in candidates}
        if decision in valid_names:
            logger.info(f"Router: Selected best match: {decision}")
            return decision

        # LAST RESORT: Simple keyword matching on names
        logger.warning("Router: No LLM match, falling back to keyword search.")
        for c in candidates:
            name_lower = c["name"].lower()
            query_lower = query.lower()
            if name_lower in query_lower or any(
                word in name_lower for word in query_lower.split()
            ):
                logger.info(f"Router: Fallback matched: {c['name']}")
                return c["name"]

        logger.warning("Router: No match found at all.")
        return None


# Singleton instance
router = IntelligenceRouter()
