# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import ast

from ..base import BaseEvaluator, EvaluationResult


class DeterministicEvaluator(BaseEvaluator):
    """
    Evaluates Python code using deterministic structural analysis (AST).
    Checks for presence of assertions and absence of "hollow" logic.
    """

    @property
    def name(self) -> str:
        return "deterministic"

    async def evaluate(self, code: str, language: str, **kwargs) -> EvaluationResult:
        lang = language.lower()
        if lang == "html":
            return EvaluationResult(score=100.0, reason="Skipped (Not logic-based language).")

        test_code = kwargs.get("test_code", "")
        reasons = []
        score = 100.0

        # 1. Multi-Language Assertion Detection
        if lang == "python":
            assertion_count = self._count_assertions_python(test_code)
            is_valid_test = self._verify_test_calls_code_python(code, test_code)
        else:
            # Basic support for JS/C++/Java assertions via Regex
            assertion_count = self._count_assertions_regex(test_code, lang)
            is_valid_test = True  # Structural check only for non-python for now
            reasons.append(
                f"Notice: Deterministic audit for '{lang}' uses "
                "structural pattern matching (Level 2)."
            )

        # 2. Hollow Logic Detection (Python only for now)
        hollow_methods = self._find_hollow_methods(code) if lang == "python" else []
        heavy_imports = self._find_heavy_imports(code) if lang == "python" else []

        # -- Scoring Logic --

        # A. Zero Assertion Rule (Hard Reject)
        if assertion_count == 0:
            score = 0.0
            reasons.append(
                "CRITICAL: No assertions found in test code. Testing is performative only."
            )
        elif assertion_count < 3:
            score -= (3 - assertion_count) * 20
            reasons.append(f"Low test density: only {assertion_count} assertions found.")
        else:
            reasons.append(f"Satisfactory test density ({assertion_count} assertions).")

        # B. Call Graph Verification (Anti-Theater)
        if lang == "python" and assertion_count > 0 and not is_valid_test:
            score *= 0.5  # Severe penalty for not calling the code
            reasons.append(
                "THEATER WARNING: Test code has assertions but NEVER CALLS "
                "any function from the target logic."
            )

        # C. Hollow Logic Penalty
        if hollow_methods:
            penalty = min(len(hollow_methods) * 30, 80)
            score -= penalty
            reasons.append(f"Hollow logic detected in methods: {', '.join(hollow_methods)}")

        # D. Performance Warning
        if heavy_imports:
            score -= min(len(heavy_imports) * 5, 20)
            reasons.append(
                f"Performance Warning: Heavy imports detected ({', '.join(heavy_imports)})."
            )

        score = max(0.0, score)

        return EvaluationResult(
            score=score,
            reason=" | ".join(reasons),
            details={
                "assertion_count": assertion_count,
                "hollow_methods": hollow_methods,
                "heavy_imports": heavy_imports,
                "is_valid_test": is_valid_test,
            },
        )

    def _count_assertions_python(self, test_code: str) -> int:
        if not test_code.strip():
            return 0
        try:
            tree = ast.parse(test_code)
            count = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    if not self._is_constant_expr(node.test):
                        count += 1
                elif (
                    isinstance(node, ast.Call)
                    and self._is_assert_call(node)
                    and not self._is_theatrical_call(node)
                ):
                    count += 1
            return count
        except SyntaxError:
            return 0

    def _is_assert_call(self, node: ast.Call) -> bool:
        prefixes = ["assert", "expect", "assume", "verify", "should"]
        if isinstance(node.func, ast.Name):
            return any(node.func.id.startswith(p) for p in prefixes)
        if isinstance(node.func, ast.Attribute):
            return any(node.func.attr.startswith(p) for p in prefixes)
        return False

    def _is_theatrical_call(self, node: ast.Call) -> bool:
        """Checks if a call is 'testing theater' (e.g. assert_equal(1, 1))."""
        has_args = len(node.args) > 0 or len(node.keywords) > 0
        if not has_args:
            return False

        all_args_constant = all(self._is_constant_expr(arg) for arg in node.args)
        all_kw_constant = all(self._is_constant_expr(kw.value) for kw in node.keywords)
        return all_args_constant and all_kw_constant

    def _is_constant_expr(self, node: ast.AST) -> bool:
        """Determines if an expression is evaluation-time constant (trivial)."""
        # Handle Python 3.8+ Constant node
        if hasattr(ast, "Constant") and isinstance(node, ast.Constant):
            return True
        # Handle older Python and specific constant-like structures
        if isinstance(node, (ast.Num, ast.Str, ast.Bytes, ast.NameConstant)):
            return True
        # Handle common trivial comparisons: 1 == 1, True is True
        return bool(
            isinstance(node, ast.Compare)
            and self._is_constant_expr(node.left)
            and all(self._is_constant_expr(comp) for comp in node.comparators)
        )

    def _verify_test_calls_code_python(self, code: str, test_code: str) -> bool:
        """Checks if test_code calls any function or class defined in code."""
        try:
            code_tree = ast.parse(code)
            test_tree = ast.parse(test_code)

            # Find all public definitions in code
            defined_names = set()
            for node in ast.walk(code_tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ) and not node.name.startswith("_"):
                    defined_names.add(node.name)

            if not defined_names:
                return True  # Nothing defined to call

            # Check if any defined name is called or referenced in test_code
            for node in ast.walk(test_tree):
                if isinstance(node, ast.Name) and node.id in defined_names:
                    return True
                if isinstance(node, ast.Attribute) and node.attr in defined_names:
                    return True
            return False
        except SyntaxError:
            return True  # Fallback on error

    def _count_assertions_regex(self, test_code: str, lang: str) -> int:
        """Fallback assertion counter using Regex for non-Python languages."""
        import re

        patterns = {
            "javascript": r"(expect|assert)(?:\.\w+)*\(.*?\)",
            "typescript": r"(expect|assert)(?:\.\w+)*\(.*?\)",
            "cpp": r"(assert|EXPECT_|ASSERT_)(?:\w+)*\(.*?\)",
            "c": r"(assert|assert_c)\(.*?\)",
            "java": r"assert(True|False|Equals|NotNull|Same|Null|ArrayEquals)(?:\.\w+)*\(.*?\)",
            "php": r"(assert|assertTrue|assertEquals|assertNotEquals)(?:\.\w+)*\(.*?\)",
        }

        pattern = patterns.get(lang.lower(), r"(assert|expect|assume).*?\(.*?\)")
        matches = re.findall(pattern, test_code)

        # Basic constant filtering via heuristic
        valid_matches = 0
        for m in matches:
            # Heuristic: If it looks like assert(true) or assert(1 == 1)
            inner = m.lower()
            if (
                "true" in inner or "false" in inner or "1==1" in inner or "1 == 1" in inner
            ) and len(inner) < 20:
                continue
            valid_matches += 1

        return valid_matches

    def _find_hollow_methods(self, code: str) -> list[str]:
        try:
            tree = ast.parse(code)
            hollow = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body = [
                        n
                        for n in node.body
                        if not (
                            isinstance(n, ast.Expr)
                            and isinstance(n.value, ast.Constant)
                            and isinstance(n.value.value, str)
                        )
                    ]
                    if not body:
                        hollow.append(node.name)
                        continue
                    if len(body) == 1:
                        stmt = body[0]
                        if isinstance(stmt, ast.Pass) or (
                            isinstance(stmt, ast.Expr)
                            and isinstance(stmt.value, ast.Constant)
                            and stmt.value.value is Ellipsis
                        ):
                            hollow.append(node.name)
                        elif isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Name):
                            arg_names = [a.arg for a in node.args.args]
                            if stmt.value.id in arg_names:
                                hollow.append(node.name)
            return hollow
        except SyntaxError:
            return []

    def _find_heavy_imports(self, code: str) -> list[str]:
        HEAVY_LIBS = {"torch", "tensorflow", "sklearn", "pandas", "matplotlib", "seaborn", "scipy"}
        heavy_found = []
        try:
            tree = ast.parse(code)
            for node in tree.body:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        base_mod = alias.name.split(".")[0]
                        if base_mod in HEAVY_LIBS:
                            heavy_found.append(base_mod)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    base_mod = node.module.split(".")[0]
                    if base_mod in HEAVY_LIBS:
                        heavy_found.append(base_mod)
            return list(set(heavy_found))
        except SyntaxError:
            return []
