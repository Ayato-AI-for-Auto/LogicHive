import ast
import os
import re
from pathlib import Path

from core.logging_config import get_logger

from ..base import BaseEvaluator, EvaluationResult

logger = get_logger(__name__)


class DependencyVouchEvaluator(BaseEvaluator):
    """
    Hallucinated Imports detector inspired by Rigour.
    Verifies that all imports are either stdlib, project local, or declared in manifests.
    """

    @property
    def name(self) -> str:
        return "dependency_vouch"

    async def evaluate(self, code: str, language: str, **kwargs) -> EvaluationResult:
        if language.lower() != "python":
            return EvaluationResult(score=100.0, reason="Dependency check skipped for non-python.")

        try:
            tree = ast.parse(code)
            imports = self._extract_imports(tree)
        except Exception as e:
            return EvaluationResult(score=0.0, reason=f"Syntax error: {e}")

        if not imports:
            return EvaluationResult(score=100.0, reason="No external dependencies found.")

        declared = self._get_declared_dependencies()
        hallucinated = self._find_hallucinated_imports(imports, declared)

        if not hallucinated:
            return EvaluationResult(score=100.0, reason="All dependencies are verified.")

        score = max(0.0, 100.0 - (len(hallucinated) * 30))
        return EvaluationResult(
            score=score,
            reason=f"Hallucinated imports: {', '.join(hallucinated)}",
            details={"missing": hallucinated},
        )

    def _is_stdlib(self, module_name: str) -> bool:
        std = {
            "os",
            "sys",
            "json",
            "re",
            "math",
            "datetime",
            "typing",
            "asyncio",
            "logging",
            "ast",
            "pathlib",
            "abc",
            "collections",
            "functools",
            "itertools",
            "threading",
            "multiprocessing",
            "pickle",
            "shutil",
            "tempfile",
            "time",
            "uuid",
            "hashlib",
            "base64",
            "xml",
            "html",
            "unittest",
            "pytest",
            "typing_extensions",
            "random",
            "enum",
            "inspect",
            "traceback",
            "warnings",
            "importlib",
            "glob",
            "argparse",
        }
        return module_name.split(".")[0] in std

    def _get_declared_dependencies(self) -> set[str]:
        cwd = os.getcwd()
        declared = self._load_manifest_dependencies(cwd)
        if not declared:
            root = Path(__file__).parent.parent.parent.parent
            declared = self._load_manifest_dependencies(str(root))
        return declared

    def _find_hallucinated_imports(self, imports: set[str], declared: set[str]) -> list[str]:
        hallucinated = []
        cwd = os.getcwd()
        for imp in imports:
            if self._is_stdlib(imp):
                continue

            top_level = imp.split(".")[0]
            if (Path(cwd) / f"{top_level}.py").exists() or (
                Path(cwd) / top_level / "__init__.py"
            ).exists():
                continue

            normalized = top_level.lower().replace("_", "-")
            if normalized in declared:
                continue
            # Fallback for common libs if no manifest found
            if not declared and top_level in {
                "pandas",
                "numpy",
                "requests",
                "pydantic",
                "fastapi",
                "sqlalchemy",
                "tqdm",
                "yaml",
            }:
                continue

            hallucinated.append(imp)
        return hallucinated

    def _extract_imports(self, tree: ast.AST) -> set[str]:
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports.add(node.module)
        return imports

    def _load_manifest_dependencies(self, cwd: str) -> set[str]:
        deps = set()
        # 1. requirements.txt
        for req_file in ["requirements.txt", "requirements-dev.txt"]:
            path = Path(cwd) / req_file
            if path.exists():
                content = path.read_text(errors="ignore")
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith(("#", "-")):
                        continue
                    # Extract package name: e.g. "flask==2.0.1" -> "flask", "pandas>=1.0" -> "pandas"
                    # Split on any character that isn't a letter, digit, underscore, or hyphen
                    name_match = re.match(r"^([a-zA-Z0-9_\-]+)", line)
                    if name_match:
                        deps.add(name_match.group(1).lower().replace("_", "-"))

        # 2. pyproject.toml
        pyproj = Path(cwd) / "pyproject.toml"
        if pyproj.exists():
            content = pyproj.read_text(errors="ignore")
            # Simple regex search instead of full toml parser
            matches = re.findall(r"dependencies\s*=\s*\[([\s\S]*?)\]", content)
            for match in matches:
                pkgs = re.findall(r'["\']([^">=<!\s\[]+)', match)
                for p in pkgs:
                    deps.add(p.lower().replace("_", "-"))

        return deps
