# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
import importlib
import importlib.util
import os
import pkgutil
import sys
from pathlib import Path
from typing import Any, cast

from core.logging_config import get_logger

from .base import BaseEvaluator, EvaluationResult

logger = get_logger(__name__)


class EvaluationManager:
    """
    Coordinates multiple evaluators to determine the final quality score.
    Now supports dynamic plugin loading from the .plugins package.
    """

    def __init__(self):
        self.evaluators: list[BaseEvaluator] = []
        self._load_plugins()

    def _load_plugins(self):
        """
        Dynamically discovers and instantiates all BaseEvaluator subclasses.
        """
        logger.debug("EvaluationManager: _load_plugins called")
        try:
            modules = self._discover_modules()
            self._instantiate_evaluators(modules)
        except Exception as e:
            logger.error(f"EvaluationManager: Plugin discovery process failed: {e}")

    def _discover_modules(self):
        """Discovers modules via package and filesystem."""
        # --- PyInstaller Path Fix ---
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            # Bundled app: find the plugins directory recursively in _MEIPASS
            plugins_dir = None
            for root, dirs, files in os.walk(getattr(sys, "_MEIPASS")):
                if "plugins" in dirs:
                    plugins_dir = Path(os.path.join(root, "plugins"))
                    logger.debug(f"EvaluationManager: Found plugins dir at: {plugins_dir}")
                    break

            # If not found via search, fallback to historical locations
            if not plugins_dir:
                base_dir = Path(getattr(sys, "_MEIPASS"))
                # Potential locations
                potential_dirs = [
                    base_dir / "core" / "evaluation" / "plugins",
                    base_dir / "src" / "core" / "evaluation" / "plugins",
                    base_dir / "engine" / "src" / "core" / "evaluation" / "plugins"
                ]
                for p in potential_dirs:
                    if p.exists():
                        plugins_dir = p
                        break
                else:
                    # Final resort: use the first one
                    plugins_dir = potential_dirs[0]

        else:
            # Source mode: standard relative path
            plugins_dir = Path(os.path.dirname(__file__)) / "plugins"

        logger.debug(f"EvaluationManager: Searching for plugins in {plugins_dir}")

        if not plugins_dir.exists():
            logger.error(f"EvaluationManager: Plugins directory not found at {plugins_dir}")
            return []

        # 1. Try package-based discovery
        modules = self._discover_via_package()
        if modules:
            return modules

        # 2. Filesystem fallback
        return self._discover_via_filesystem(str(plugins_dir))

    def _discover_via_package(self):
        modules = []
        package_names = [
            f"{__package__}.plugins" if __package__ else None,
            "core.evaluation.plugins",
            "src.core.evaluation.plugins",
        ]
        for pkg_name in [p for p in package_names if p]:
            try:
                pkg = importlib.import_module(pkg_name)
                for _loader, name, _is_pkg in pkgutil.walk_packages(
                    pkg.__path__, pkg.__name__ + "."
                ):
                    try:
                        modules.append(importlib.import_module(name))
                    except ImportError:
                        continue
                if modules:
                    return modules
            except ImportError:
                continue
        return []

    def _discover_via_filesystem(self, plugins_dir):
        modules = []
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                file_path = os.path.join(plugins_dir, filename)
                try:
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        modules.append(mod)
                except Exception as e:
                    logger.error(f"EvaluationManager: Failed to load {filename} via fallback: {e}")
        return modules

    def _instantiate_evaluators(self, modules):
        for module in modules:
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseEvaluator)
                    and attr is not BaseEvaluator
                ):
                    try:
                        inst = attr()
                        if not any(e.name == inst.name for e in self.evaluators):
                            self.evaluators.append(inst)
                            logger.info(f"EvaluationManager: Loaded plugin '{inst.name}'")
                    except Exception as e:
                        logger.error(f"EvaluationManager: Failed to instantiate {attr_name}: {e}")

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
            return cast(dict[str, Any], {
                "score": 40.0,
                "reason": (
                    "Unverified Asset: No test code provided. "
                    "Use [AI-DRAFT] in description to skip verification check."
                ),
                "details": {"system": "Rigor Gate", "status": "missing_tests"},
            })
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
                # This case should not be reachable if evaluate() returns EvaluationResult
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
        if struct and struct.score == 0:
            return cast(dict[str, Any], {
                "score": 0.0,
                "reason": f"CRITICAL STRUCTURAL ERROR: {struct.reason}",
                "details": {"structural": struct},
                "is_system_error": struct.is_system_error,
            })

        # Security Veto
        sec = results.get("security_static")
        if sec and sec.score < 60:
            return cast(dict[str, Any], {
                "score": 0.0,
                "reason": f"SECURITY REJECTION: {sec.reason}",
                "details": self._serialize_results(results),
                "is_system_error": aggregate_system_error,
            })

        # Dependency Veto
        dep = results.get("dependency_vouch")
        if dep and dep.score < 70:
            return cast(dict[str, Any], {
                "score": 0.0,
                "reason": f"DEPENDENCY REJECTION: {dep.reason}",
                "details": self._serialize_results(results),
                "is_system_error": aggregate_system_error,
            })

        # Deterministic Veto (Syntax Errors)
        det = results.get("deterministic")
        if det and det.score == 0:
            py_stat = results.get("python_static")
            if py_stat and py_stat.score == 0 and "Syntax Error" in py_stat.reason:
                return cast(dict[str, Any], {
                    "score": 0.0,
                    "reason": f"CRITICAL SYNTAX ERROR: {py_stat.reason}",
                    "details": self._serialize_results(results),
                    "is_system_error": aggregate_system_error,
                })
            return cast(dict[str, Any], {
                "score": 0.0,
                "reason": f"DETERMINISTIC REJECTION: {det.reason}",
                "details": self._serialize_results(results),
                "is_system_error": aggregate_system_error,
            })

        # Language-specific static Veto (e.g. html_static, c_static, etc.)
        for key in ["html_static", "c_static", "java_static", "php_static"]:
            stat = results.get(key)
            if stat and stat.score == 0:
                return cast(dict[str, Any], {
                    "score": 0.0,
                    "reason": f"STATIC VALIDATION REJECTION ({key}): {stat.reason}",
                    "details": self._serialize_results(results),
                    "is_system_error": stat.is_system_error or aggregate_system_error,
                })

        # Runtime Veto
        run = results.get("runtime")
        if run and run.score == 0 and not kwargs.get("_is_draft"):
            return cast(dict[str, Any], {
                "score": 0.0,
                "reason": f"RUNTIME REJECTION: {run.reason}",
                "details": self._serialize_results(results),
                "is_system_error": run.is_system_error or aggregate_system_error,
            })

        return None

    def _calculate_weighted_score(self, results, lang, kwargs):
        parts = []
        reasons = []

        # Weights: Deterministic (30%), Runtime (30%), Static/Security (20%), AI (15%), Metrics (5%)
        mapping = {
            "deterministic": (0.30, "Facts"),
            "runtime": (0.30, "Runtime"),
            "ai_gate": (0.15, "AI Opinion"),
            "metrics_gate": (0.05, "Maintainability"),
        }

        for key, (weight, label) in mapping.items():
            res = results.get(key)
            if res:
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

        # AI Veto
        ai_res = results.get("ai_gate")
        if ai_res:
            if ai_res.score < 30:
                final_score = 0.0
                reasons.insert(
                    0,
                    "VETO: AI Auditor identified 'Quality Theater' - Opinion confirmed rejection.",
                )
            elif ai_res.score < 70:
                final_score = min(final_score, ai_res.score)

        return final_score, reasons

    def _aggregate_static_scores(self, results, lang):
        scores = []
        for key in ["security_static", "dependency_vouch"]:
            if key in results:
                scores.append(results[key].score)

        if lang == "python":
            if "ruff" in results:
                scores.append(results["ruff"].score)
            elif "python_static" in results:
                scores.append(results["python_static"].score)
        elif "eslint" in results:
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
        return cast(dict[str, Any], {
            "score": final_score,
            "reason": " | ".join(reasons),
            "details": self._serialize_results(results),
            "is_system_error": aggregate_system_error,
        })
