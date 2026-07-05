from core.config import GEMINI_API_KEY
from core.consolidation import LogicIntelligence
from core.logging_config import get_logger

from ..base import BaseEvaluator, EvaluationResult

logger = get_logger(__name__)


class AIGateEvaluator(BaseEvaluator):
    """
    Evaluates code quality using LLM-based logic gate.
    """

    @property
    def name(self) -> str:
        return "ai_gate"

    def __init__(self, api_key: str = GEMINI_API_KEY, intel: LogicIntelligence | None = None):
        self.intel = intel or LogicIntelligence(api_key)

    async def evaluate(self, code: str, language: str, **kwargs) -> EvaluationResult:
        try:
            test_code = kwargs.get("test_code", "")
            quality = await self.intel.evaluate_quality(code, test_code=test_code)
            score = float(quality.get("score", 0))
            reason = quality.get("reason", "No reason provided by AI.")
            # Store raw output and provider info in details
            details = {
                "raw_output": quality.get("raw_output"),
                "provider_info": quality.get("provider_info")
            }
            return EvaluationResult(score=score, reason=reason, details=details)
        except Exception as e:
            logger.error(f"AIGateEvaluator: AI Evaluation failed: {e}")
            return EvaluationResult(
                score=None, reason=f"AI Provider Transient Error: {e}", is_system_error=True
            )
