# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
import importlib.metadata
import os
import sys
from typing import Any, cast

from core.logging_config import get_logger

from .base import BaseEvaluator, EvaluationResult

logger = get_logger(__name__)

# Entry point group name for evaluator plugins
EVALUATOR_ENTRY_POINT_GROUP = "logichive.evaluators"

# Built-in evaluator modules (for backward compatibility and explicit registration)
BUILTIN_EVALUATORS = [
    "core.evaluation.plugins.deterministic:DeterministicEvaluator",
    "core.evaluation.plugins.static:PythonStaticEvaluator",
    "core.evaluation.plugins.static:RuffEvaluator",
    "core.evaluation.plugins.security_static:SecurityStaticEvaluator",
    "core.evaluation.plugins.runtime:RuntimeEvaluator",
    "core.evaluation.plugins.metrics_gate:MetricsGateEvaluator",
    "core.evaluation.plugins.dependency_vouch:DependencyVouchEvaluator",
    "core.evaluation.plugins.ai:AIGateEvaluator",
]


class EvaluationManager:
    """
    Coordinates multiple evaluators to determine the final quality score.
    Uses entry points for plugin discovery (replaces fragile filesystem scanning).
    """

    def __init__(self):
        self.evaluators: list[BaseEvaluator] = []
        self._load_plugins()

    def _load_plugins(self):
        """
        Loads evaluator plugins via entry points with fallback to built-in list.
        """
        logger.debug("EvaluationManager: Loading plugins via entry points")
        loaded = False

        # 1. Try entry points (setuptools / pip installed packages)
        try:
            eps = importlib.metadata.entry_points(group=EVALUATOR_ENTRY_POINT_GROUP)
            for ep in eps:
                try:
                    evaluator_class = ep.load()
                    if issubclass(evaluator_class, BaseEvaluator) and evaluator_class is not BaseEvaluator:
                        inst = evaluator_class()
                        if not any(e.name == inst.name for e in self.evaluators):
                            self.evaluators.append(inst)
                            logger.info(f"EvaluationManager: Loaded plugin '{inst.name}' via entry point '{ep.name}'")
                            loaded = True
                except Exception as e:
                    logger.error(f"EvaluationManager: Failed to load entry point '{ep.name}': {e}")
        except Exception as e:
            logger.debug(f"EvaluationManager: Entry point discovery failed (expected in dev): {e}")

        # 2. Fallback: explicit built-in evaluators (works in source and frozen)
        if not loaded:
            logger.debug("EvaluationManager: Falling back to built-in evaluator list")
            for spec in BUILTIN_EVALUATORS:
                try:
                    module_path, class_name = spec.split(":")
                    module = __import__(module_path, fromlist=[class_name])
                    evaluator_class = getattr(module, class_name)
                    if issubclass(evaluator_class, BaseEvaluator):
                        inst = evaluator_class()
                        if not any(e.name == inst.name for e in self.evaluators):
                            self.evaluators.append(inst)
                            logger.info(f"EvaluationManager: Loaded built-in plugin '{inst.name}'")
                except Exception as e:
                    logger.error(f"EvaluationManager: Failed to load built-in '{spec}': {e}")

        # Sort evaluators by priority if they have it (lower = runs first)
        self.evaluators.sort(key=lambda e: getattr(e, "priority", 100))

        logger.info(f"EvaluationManager: Total evaluators loaded: {len(self.evaluators)}")

    def get_evaluator(self, name: str) -> BaseEvaluator | None:
        """Returns a loaded evaluator by its name."""
        for ev in self.evaluators:
            if ev.name == name:
                return ev
        return None

    async def evaluate_all(self, code: str, language: str, **kwargs) -> dict[str, Any]:
        """
        Runs all applicable evaluators and merges results.
        """
        lang = language.lower()

        # 1. Pre-evaluation checks
        pre_check = self._perform_pre_checks(lang, kwargs)
        if pre_check:
            return pre_check

        # 2. Run evaluators
        results = await self._run_evaluators(code, lang, **kwargs)

        # 3. Handle immediate rejections (Security, Dependency, Structural)
        rejection = self._check_critical_rejections(results, language, **kwargs)
        if rejection:
            return rejection

        # 4. Calculate weighted score
        final_score, reasons = self._calculate_weighted_score(results, lang, kwargs)

        # 5. Build final report
        return self._build_final_report(final_score, reasons, results)

    def _perform_pre_checks(self, lang: str, kwargs: dict[str, Any]) -> dict[str, Any] | None:
        desc = (kwargs.get("description") or "").upper()
        is_draft = kwargs.get("is_draft", False) or any(
            k in desc for k in ["DRAFT", "AI_DRAFT", "AI-DRAFT"]
        )
        test_code = kwargs.get("test_code", "")

        if not is_draft and not test_code and lang != "html":
            return cast(
                dict[str, Any],
                {
                    "score": 40.0,
                    "reason": (
                        "Unverified Asset: No test code provided. "
                        "Use [AI-DRAFT] in description to skip verification check."
                    ),
                    "details": {"system": "Rigor Gate", "status": "missing_tests"},
                },
            )
        kwargs["_is_draft"] = is_draft  # Internal use
        return None

    async def _run_evaluators(self, code: str, lang: str, **kwargs) -> dict[str, EvaluationResult]:
        results: dict[str, EvaluationResult] = {}
        tasks = []
        eval_map = {}

        for ev in self.evaluators:
            tasks.append(ev.evaluate(code, lang, **kwargs))
            eval_map[len(tasks) - 1] = ev.name

        eval_outputs = await asyncio.gather(*tasks, return_exceptions=True)

        for i, res in enumerate(eval_outputs):
            name = eval_map[i]
            if isinstance(res, Exception):
                logger.error(f"EvaluationManager: Evaluator '{name}' failed: {res}")
                results[name] = EvaluationResult(
                    score=0.0, reason=f"Evaluator error: {res}", is_system_error=True
                )
            elif isinstance(res, EvaluationResult):
                results[name] = res
            else:
                results[name] = EvaluationResult(
                    score=0.0, reason="Unexpected internal result type", is_system_error=True
                )
        return results

    def _check_critical_rejections(
        self, results: dict[str, EvaluationResult], language: str, **kwargs: Any
    ) -> dict[str, Any] | None:
        aggregate_system_error = any(v.is_system_error for v in results.values())

        # Structural Veto
        struct = results.get("structural")
        if struct and struct.score is not None and struct.score == 0:
            return cast(
                dict[str, Any],
                {
                    "score": 0.0,
                    "reason": f"CRITICAL STRUCTURAL ERROR: {struct.reason}",
                    "details": {"structural": struct},
                    "is_system_error": struct.is_system_error,
                },
            )

        # Security Veto
        sec = results.get("security_static")
        if sec and sec.score is not None and sec.score < 60:
            return cast(
                dict[str, Any],
                {
                    "score": 0.0,
                    "reason": f"SECURITY REJECTION: {sec.reason}",
                    "details": self._serialize_results(results),
                    "is_system_error": aggregate_system_error,
                },
            )

        # Dependency Veto
        dep = results.get("dependency_vouch")
        if dep and dep.score is not None and dep.score < 70:
            return cast(
                dict[str, Any],
                {
                    "score": 0.0,
                    "reason": f"DEPENDENCY REJECTION: {dep.reason}",
                    "details": self._serialize_results(results),
                    "is_system_error": aggregate_system_error,
                },
            )

        # Deterministic Veto (Syntax Errors)
        det = results.get("deterministic")
        if det and det.score is not None and det.score == 0:
            py_stat = results.get("python_static")
            if (
                py_stat
                and py_stat.score is not None
                and py_stat.score == 0
                and "Syntax Error" in py_stat.reason
            ):
                return cast(
                    dict[str, Any],
                    {
                        "score": 0.0,
                        "reason": f"CRITICAL SYNTAX ERROR: {py_stat.reason}",
                        "details": self._serialize_results(results),
                        "is_system_error": aggregate_system_error,
                    },
                )
            return cast(
                dict[str, Any],
                {
                    "score": 0.0,
                    "reason": f"DETERMINISTIC REJECTION: {det.reason}",
                    "details": self._serialize_results(results),
                    "is_system_error": aggregate_system_error,
                },
            )

        # Language-specific static Veto (e.g. html_static, c_static, etc.)
        for key in ["html_static", "c_static", "java_static", "php_static"]:
            stat = results.get(key)
            if stat and stat.score is not None and stat.score == 0:
                return cast(
                    dict[str, Any],
                    {
                        "score": 0.0,
                        "reason": f"STATIC VALIDATION REJECTION ({key}): {stat.reason}",
                        "details": self._serialize_results(results),
                        "is_system_error": stat.is_system_error or aggregate_system_error,
                    },
                )

        # Runtime Veto
        run = results.get("runtime")
        if run and run.score is not None and run.score == 0 and not kwargs.get("_is_draft"):
            return cast(
                dict[str, Any],
                {
                    "score": 0.0,
                    "reason": f"RUNTIME REJECTION: {run.reason}",
                    "details": self._serialize_results(results),
                    "is_system_error": run.is_system_error or aggregate_system_error,
                },
            )

        return None

    def _calculate_weighted_score(self, results, lang, kwargs):
        parts = []
        reasons = []

        # Configurable AI Gate weight (default 10%, was 15%)
        ai_gate_weight = float(os.getenv("AI_GATE_WEIGHT", "0.10"))

        # Weights: Deterministic (30%), Runtime (30%), Static/Security (20%), AI (10%), Metrics (5%)
        mapping = {
            "deterministic": (0.30, "Facts"),
            "runtime": (0.30, "Runtime"),
            "ai_gate": (ai_gate_weight, "AI Opinion"),
            "metrics_gate": (0.05, "Maintainability"),
        }

        for key, (weight, label) in mapping.items():
            res = results.get(key)
            if res:
                # Skip system errors (score=None) in weighted calculation
                if res.is_system_error and res.score is None:
                    reasons.append(f"{label}: Skipped (system error: {res.reason})")
                    continue
                parts.append((res.score, weight, f"{label}: {res.reason}"))

        # Complex static aggregation
        static_score = self._aggregate_static_scores(results, lang)
        if static_score is not None:
            parts.append(
                (
                    static_score,
                    0.20,
                    f"Rigour Static: Security/Dependency verified (Avg={static_score:.1f})",
                )
            )

        total_weight = sum(p[1] for p in parts)
        if total_weight <= 0:
            return 0.0, ["No applicable evaluators succeeded."]

        final_score = sum(score * (weight / total_weight) for score, weight, _ in parts)
        reasons = [p[2] for p in parts]

        # AI Veto (softened per ADR-0032)
        ai_res = results.get("ai_gate")
        if ai_res and not ai_res.is_system_error and ai_res.score is not None:
            if ai_res.score < 30:
                # 50% penalty instead of hard veto (was: final_score = 0.0)
                final_score *= 0.5
                reasons.insert(
                    0,
                    "AI Auditor: Quality Theater suspected (50% penalty applied)",
                )
            elif ai_res.score < 70:
                # Soft cap with 20% headroom (was: hard cap at ai_score)
                soft_cap = ai_res.score * 1.2
                final_score = min(final_score, soft_cap)
                reasons.append(f"AI Auditor: Soft cap applied at {soft_cap:.0f}")

        return final_score, reasons

    def _aggregate_static_scores(self, results, lang):
        scores = []
        for key in ["security_static", "dependency_vouch"]:
            if key in results and results[key].score is not None:
                scores.append(results[key].score)

        if lang == "python":
            if "ruff" in results and results["ruff"].score is not None:
                scores.append(results["ruff"].score)
            elif "python_static" in results and results["python_static"].score is not None:
                scores.append(results["python_static"].score)
        elif "eslint" in results and results["eslint"].score is not None:
            scores.append(results["eslint"].score)

        return sum(scores) / len(scores) if scores else None

    def _serialize_results(self, results):
        return {
            k: {
                "score": v.score,
                "reason": v.reason,
                "details": v.details,
                "is_system_error": v.is_system_error,
            }
            for k, v in results.items()
        }

    def _build_final_report(
        self, final_score: float, reasons: list[str], results: dict[str, EvaluationResult]
    ) -> dict[str, Any]:
        aggregate_system_error = any(v.is_system_error for v in results.values())
        return cast(
            dict[str, Any],
            {
                "score": final_score,
                "reason": " | ".join(reasons),
                "details": self._serialize_results(results),
                "is_system_error": aggregate_system_error,
            },
        )