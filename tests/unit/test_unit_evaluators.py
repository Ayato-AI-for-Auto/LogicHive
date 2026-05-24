import pytest

from core.evaluation.plugins.deterministic import DeterministicEvaluator
from core.evaluation.plugins.security_static import SecurityStaticEvaluator


@pytest.mark.asyncio
async def test_deterministic_evaluator_pass():
    """UNIT: Verify that deterministic evaluator passes valid code with assertions."""
    evaluator = DeterministicEvaluator()
    code = "def add(a, b):\n    return a + b"
    test_code = "def test_add():\n    assert add(1, 2) == 3\n    assert add(0, 0) == 0\n    assert add(-1, -1) == -2"

    result = await evaluator.evaluate(code, language="python", test_code=test_code)
    assert result.score >= 50, "Should score adequately for having assertions."


@pytest.mark.asyncio
async def test_deterministic_evaluator_no_assertions():
    """UNIT: Verify that lack of assertions returns a zero score."""
    evaluator = DeterministicEvaluator()
    code = "def do_nothing():\n    pass"
    test_code = "def test_do_nothing():\n    do_nothing()"

    result = await evaluator.evaluate(code, language="python", test_code=test_code)
    assert result.score == 0
    assert "assertions" in result.reason.lower()


@pytest.mark.asyncio
async def test_deterministic_evaluator_syntax_error():
    """UNIT: Verify syntax errors are caught cleanly."""
    evaluator = DeterministicEvaluator()
    code = "def good(): pass"
    test_code = "def bad_syntax(:"

    result = await evaluator.evaluate(code, language="python", test_code=test_code)
    assert result.score == 0


@pytest.mark.asyncio
async def test_security_evaluator_blocks_eval():
    """UNIT: Verify security evaluator blocks dangerous builtins like eval/exec."""
    evaluator = SecurityStaticEvaluator()
    code = "def dangerous(x):\n    return eval(x)"
    test_code = "def test_dangerous():\n    assert dangerous('1+1') == 2"

    result = await evaluator.evaluate(code, language="python", test_code=test_code)
    assert result.score <= 60  # Penalizes high severity
    assert (
        "eval" in result.reason.lower()
        or "security" in result.reason.lower()
        or "flaw" in result.reason.lower()
    )


@pytest.mark.asyncio
async def test_security_evaluator_pass():
    """UNIT: Verify safe code passes security gate."""
    evaluator = SecurityStaticEvaluator()
    code = "def safe(x):\n    return int(x)"
    test_code = "def test_safe():\n    assert safe('1') == 1"

    result = await evaluator.evaluate(code, language="python", test_code=test_code)
    assert result.score == 100
