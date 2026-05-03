import logging
from typing import Any

from .base import BaseEvaluator, EvaluationResult
from .plugins.deterministic import DeterministicEvaluator
from .plugins.metrics import MetricsEvaluator
from .plugins.python_static import PythonStaticEvaluator
from .plugins.runtime import RuntimeEvaluator
from .plugins.structural import StructuralEvaluator

logger = logging.getLogger(__name__)


class EvaluationManager:
    """
    Coordinates multiple evaluation plugins to score a code asset.
    The goal is to determine if the code is safe, functional, and of high quality.
    """

    def __init__(self):
        # Initialize plugins
        self.evaluators: list[BaseEvaluator] = [
            StructuralEvaluator(),
            PythonStaticEvaluator(),
            DeterministicEvaluator(),
            RuntimeEvaluator(),
            MetricsEvaluator(),
        ]

    async def evaluate_all(
        self,
        code: str,
        language: str,
        test_code: str | None = None,
        dependencies: list[str] | None = None,
        mock_imports: list[str] | None = None,
        timeout: int = 60,
        is_draft: bool = False,
    ) -> dict[str, Any]:
        """
        Runs all evaluators and returns a consolidated report.
        Args:
            code: Source code.
            language: Code language.
            test_code: Optional tests.
            dependencies: External packages.
            mock_imports: Imports to mock.
            timeout: Execution timeout.
            is_draft: If True, failing runtime doesn't auto-reject.
        """
        results = {}
        lang = language.lower()

        # Step 1: Structural & Static Analysis (Fast)
        # These are pre-requisites. If they fail, we stop.
        structural = next((e for e in self.evaluators if e.name == "structural"), None)
        if structural:
            struct_res = await structural.evaluate(code, lang)
            if struct_res.score == 0:
                return {
                    "score": 0.0,
                    "reason": f"CRITICAL STRUCTURAL ERROR: {struct_res.reason}",
                    "details": {"structural": struct_res},
                    "is_system_error": struct_res.is_system_error,
                }
            results["structural"] = struct_res

        # Step 2: Language Specific Static Analysis
        if lang == "python":
            python_static = next(
                (e for e in self.evaluators if e.name == "python_static"), None
            )
            if python_static:
                static_res = await python_static.evaluate(code, lang)
                results["python_static"] = static_res

        # Step 3: Run Remaining Evaluators in Parallel
        # (Deterministic, Runtime, Metrics)
        remaining = [
            e
            for e in self.evaluators
            if e.name not in ["structural", "python_static"]
        ]

        kwargs = {
            "test_code": test_code,
            "dependencies": dependencies,
            "mock_imports": mock_imports,
            "timeout": timeout,
        }

        # Execute evaluations
        eval_tasks = [e.evaluate(code, lang, **kwargs) for e in remaining]
        eval_outputs = await asyncio.gather(*eval_tasks, return_exceptions=True)

        for evaluator, output in zip(remaining, eval_outputs):
            if isinstance(output, Exception):
                logger.error(f"Evaluator {evaluator.name} crashed: {output}")
                results[evaluator.name] = EvaluationResult(
                    score=0,
                    reason=f"Internal Evaluator Error: {str(output)}",
                    is_system_error=True,
                )
            else:
                results[evaluator.name] = output

        # Check for system errors in critical gates even if score isn't 0
        aggregate_system_error = any(v.is_system_error for v in results.values())

        # 4. Weighted Calculation
        # Weights: Deterministic (30%), Runtime (30%), Static/Security (20%), AI (15%), Metrics (5%)
        parts = []

        # A. Deterministic Layer (30%) - THE TRUTH FOUNDATION
        det_res = results.get("deterministic")
        if det_res:
            det_score = det_res.score
            if det_score == 0:
                # ABSOLUTE VETO: If PythonStatic found a syntax error, prioritize it over 'No assertions'
                python_static = results.get("python_static")
                if python_static and python_static.score == 0 and "Syntax Error" in python_static.reason:
                    return {
                        "score": 0.0,
                        "reason": f"CRITICAL SYNTAX ERROR: {python_static.reason}",
                        "details": {
                            k: {"score": v.score, "reason": v.reason, "details": v.details}
                            for k, v in results.items()
                        },
                    }

                return {
                    "score": 0.0,
                    "reason": f"DETERMINISTIC REJECTION: {det_res.reason}",
                    "details": {
                        k: {"score": v.score, "reason": v.reason, "details": v.details}
                        for k, v in results.items()
                    },
                }
            parts.append((det_score, 0.30, f"Facts: {det_res.reason}"))

        # B. Runtime Verification (30%)
        runtime_res = results.get("runtime")
        if runtime_res:
            runtime_score = runtime_res.score
            if runtime_score == 0 and not is_draft:
                return {
                    "score": 0.0,
                    "reason": f"Critical Logic Failure (Verified Asset): {runtime_res.reason}",
                    "details": {
                        k: {"score": v.score, "reason": v.reason, "details": v.details}
                        for k, v in results.items()
                    },
                }
            parts.append((runtime_score, 0.30, f"Execution: {runtime_res.reason}"))

        # C. Static/Structural (20%)
        # Combine structural and language-specific static
        static_total = 0.0
        static_count = 0
        if "structural" in results:
            static_total += results["structural"].score
            static_count += 1
        if "python_static" in results:
            static_total += results["python_static"].score
            static_count += 1

        if static_count > 0:
            avg_static = static_total / static_count
            parts.append((avg_static, 0.20, "Static Analysis and Standards"))

        # D. Metrics (5%)
        metrics_res = results.get("metrics")
        if metrics_res:
            parts.append((metrics_res.score, 0.05, f"Complexity: {metrics_res.reason}"))

        # E. AI Intuition (15%) - Placeholder for LLM-based grading
        # Currently defaults to 100 or based on static score
        parts.append((100.0, 0.15, "AI-Grading: Heuristics based logic integrity"))

        # 5. Final Aggregation
        weighted_score = 0.0
        applied_weight = 0.0
        reasons = []

        for score, weight, reason in parts:
            weighted_score += score * weight
            applied_weight += weight
            if score < 70:
                reasons.append(reason)

        if applied_weight > 0:
            final_score = weighted_score / applied_weight
        else:
            final_score = 0.0

        return {
            "score": round(final_score, 2),
            "reason": "; ".join(reasons) if reasons else "Quality Gate Passed",
            "details": {
                k: {"score": v.score, "reason": v.reason, "details": v.details}
                for k, v in results.items()
            },
            "is_system_error": aggregate_system_error,
        }
