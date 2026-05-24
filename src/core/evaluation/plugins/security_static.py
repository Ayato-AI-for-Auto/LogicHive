import ast
import re

from core.logging_config import get_logger

from ..base import BaseEvaluator, EvaluationResult

logger = get_logger(__name__)


class SecurityStaticEvaluator(BaseEvaluator):
    """
    Deterministic security auditor inspired by Rigour's SecurityVisitor.
    Performs AST analysis to detect structural vulnerabilities without LLM guessing.
    """

    @property
    def name(self) -> str:
        return "security_static"

    async def evaluate(self, code: str, language: str, **kwargs) -> EvaluationResult:
        if language.lower() != "python":
            return EvaluationResult(
                score=100.0, reason="Security static analysis skipped for non-python language."
            )

        issues = []
        try:
            tree = ast.parse(code)
            visitor = SecurityVisitor(code)
            visitor.visit(tree)
            visitor.check_sql_injection()
            issues = visitor.issues
        except SyntaxError as e:
            return EvaluationResult(
                score=0.0, reason=f"Logic Error (Syntax Error): {e}", is_system_error=False
            )
        except Exception as e:
            logger.error(f"SecurityStaticEvaluator: Structural analysis failed: {e}")
            return EvaluationResult(
                score=0.0, reason=f"Infrastructure Error (AST parsing): {e}", is_system_error=True
            )

        if not issues:
            return EvaluationResult(
                score=100.0, reason="No structural security vulnerabilities detected."
            )

        # Scoring: Deduct 40 points per CRITICAL issue, 10 per WEAK issue
        score = 100.0
        details = []
        for issue in issues:
            severity = issue.get("severity", "high")
            deduction = 40.0 if severity == "high" else 10.0
            score -= deduction
            details.append(f"L{issue['lineno']}: {issue['message']}")

        score = max(0.0, score)
        return EvaluationResult(
            score=score,
            reason=f"Security flaws detected: {'; '.join(details)}",
            details={"vulnerabilities": issues},
        )


class SecurityVisitor(ast.NodeVisitor):
    def __init__(self, content: str):
        self.issues = []
        self.content = content
        self.lines = content.split("\n")

    def visit_Assign(self, node: ast.Assign):
        """Detect hardcoded secrets."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id.upper()
                # Targets: API_KEY, PASSWORD, TOKEN, SECRET, etc.
                pattern = r"(API_KEY|PASSWORD|TOKEN|AUTH_TOKEN|PRIVATE_KEY|AWS_SECRET|SECRET_KEY)"
                if re.search(pattern, name) and isinstance(node.value, (ast.Constant, ast.Str)):
                    val = node.value.value if isinstance(node.value, ast.Constant) else node.value.s
                    if isinstance(val, str) and len(val) > 4:  # Ignore very short strings
                        self.issues.append(
                            {
                                "issue": "hardcoded_secret",
                                "lineno": node.lineno,
                                "severity": "high",
                                "message": f"Potential hardcoded secret in variable '{target.id}'",
                            }
                        )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Detect dangerous function calls."""
        func_name = self._resolve_func_name(node)

        # 1. Code Injection
        if func_name in ("eval", "exec"):
            self._add_issue("code_injection", node.lineno, f"Dangerous usage of '{func_name}'")

        # 2. Insecure Deserialization
        if func_name in ("loads", "load") and self._is_pickle_call(node):
            self._add_issue("insecure_deserialization", node.lineno, "Pickle usage is insecure")

        # 3. Command Injection
        if func_name in (
            "run",
            "call",
            "Popen",
            "check_call",
            "check_output",
        ) and self._has_shell_true(node):
            self._add_issue(
                "command_injection", node.lineno, f"Subprocess '{func_name}' with shell=True"
            )

        self.generic_visit(node)

    def _resolve_func_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _is_pickle_call(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            return node.func.value.id == "pickle"
        return False

    def _has_shell_true(self, node: ast.Call) -> bool:
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                return True
        return False

    def _add_issue(self, issue_type, lineno, message, severity="high"):
        self.issues.append(
            {
                "issue": issue_type,
                "lineno": lineno,
                "severity": severity,
                "message": message,
            }
        )

    def check_sql_injection(self):
        """Regex-based catch for obvious SQL injection patterns."""
        patterns = [
            (r"\.execute\(f[\"']", "F-string SQL query"),
            (r"\.execute\(.*\%", "String formatting (%) in SQL query"),
            (r"\.execute\(.*\+", "String concatenation in SQL query"),
        ]
        for pattern, msg in patterns:
            for i, line in enumerate(self.lines, 1):
                if re.search(pattern, line):
                    self.issues.append(
                        {
                            "issue": "sql_injection",
                            "lineno": i,
                            "severity": "high",
                            "message": f"Potential SQL injection detected: {msg}",
                        }
                    )
