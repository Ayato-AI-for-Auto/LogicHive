import logging
from typing import Dict, List, Optional

from core.config import (
    GEMINI_API_KEY,
    MODEL_TYPE,
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
)

logger = logging.getLogger(__name__)


class IntelligenceRouter:
    """
    Reranks search results to find the best match for a natural language intent.
    Uses 'Reverse Intelligence': Hub generates prompts, Client executes.
    """

    def get_prompt(self, query: str, candidates: List[Dict]) -> str:
        """
        Generates the prompt template for the client to execute.
        This contains the secret logic/instruction for reranking.
        """
        if not candidates:
            return ""

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
        return prompt

    def finalize_decision(self, candidates: List[Dict], llm_output: str) -> Optional[str]:
        """
        Parses the LLM output (executed by client) and ensures the result is a valid candidate.
        """
        if not candidates or not llm_output:
            return None

        # Cleanup decision (sometimes LLMs add extra text)
        decision = llm_output.split("\n")[0].strip().replace("'", "").replace('"', "")

        valid_names = {c["name"] for c in candidates}
        if decision in valid_names:
            logger.info(f"Router: Selected best match: {decision}")
            return decision

        logger.warning(f"Router: LLM output '{decision}' did not match any candidate.")
        return None


# Singleton instance
router = IntelligenceRouter()
