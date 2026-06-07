import pytest

from core.evaluation.manager import EvaluationManager
from core.evaluation.plugins.static import PythonStaticEvaluator


@pytest.mark.asyncio
async def test_python_static_evaluator_clean_code():
    """UNIT: Verify that simple clean code passes PythonStaticEvaluator with a perfect score."""
    evaluator = PythonStaticEvaluator()
    code = "def calculate_sum(a, b):\n    return a + b"
    res = await evaluator.evaluate(code, language="python")
    assert res.score == 100.0
    assert "passed" in res.reason.lower()


@pytest.mark.asyncio
async def test_python_static_evaluator_relative_import():
    """UNIT: Verify that relative imports penalize the score."""
    evaluator = PythonStaticEvaluator()
    code = "from .utils import helper\ndef run():\n    return helper()"
    res = await evaluator.evaluate(code, language="python")
    assert res.score == 90.0
    assert "relative import" in res.reason.lower()


@pytest.mark.asyncio
async def test_python_static_evaluator_deep_import():
    """UNIT: Verify that deep imports penalize the score."""
    evaluator = PythonStaticEvaluator()
    code = "import urllib.request\ndef fetch():\n    pass"
    res = await evaluator.evaluate(code, language="python")
    assert res.score == 95.0
    assert "deep import" in res.reason.lower()


@pytest.mark.asyncio
async def test_python_static_evaluator_multi_function_penalty():
    """UNIT: Verify that multiple functions penalize the atomicity check."""
    evaluator = PythonStaticEvaluator()
    code = "def first():\n    pass\ndef second():\n    pass"
    res = await evaluator.evaluate(code, language="python")
    assert res.score == 90.0
    assert "atomicity risk" in res.reason.lower()


@pytest.mark.asyncio
async def test_evaluation_manager_veto_logic():
    """UNIT: Verify critical vetos under EvaluationManager."""
    manager = EvaluationManager()

    # If security evaluator returns score < 60, we expect score = 0.0 (Security Veto)
    # We will trigger evaluate_all and check vetoing.
    code = "def dangerous(x):\n    eval(x)\n    exec(x)"
    test_code = "def test_dangerous():\n    assert True\n    assert True\n    assert True"
    res = await manager.evaluate_all(
        code=code,
        language="python",
        description="test function",
        test_code=test_code
    )
    assert res["score"] == 0.0
    assert "SECURITY" in res["reason"] or "Veto" in res["reason"] or "Ruff" in res["reason"] or "Syntax Error" in res["reason"]
