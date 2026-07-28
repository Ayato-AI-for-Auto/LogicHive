import json
import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


class VerificationEvaluator:
    def __init__(self, check_score_only_func):
        self.check_score_only = check_score_only_func

    def finalize_verification(
        self,
        name: str,
        code: str,
        llm_output: str,
        description: str = "",
        dependencies: List[str] = None,
    ) -> Dict[str, Any]:
        """Combines Ruff static analysis with LLM-provided qualitative score."""
        # 1. Static Analysis (Hub-safe)
        report = self.check_score_only(name, code, description, dependencies)

        # 2. Extract LLM quantitative/qualitative data
        try:
            json_match = re.search(r"\{.*\}", llm_output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                ai_score = data.get("score", 50)
                ai_feedback = data.get("feedback", "")

                # Combine scores (Static 50% + AI 50%)
                report["final_score"] = int((report["final_score"] + ai_score) / 2)
                report["metadata"]["quality_feedback"] = (
                    f"AI: {ai_feedback} | Hub: {report['formatter']['feedback']}"
                )
        except Exception as e:
            logger.warning(f"QualityGate: Failed to parse LLM finalization: {e}")

        # Re-evaluate reliability tier
        if report["final_score"] >= 80:
            report["reliability"] = "high"
        elif report["final_score"] >= 50:
            report["reliability"] = "medium"
        else:
            report["reliability"] = "low"

        return report
