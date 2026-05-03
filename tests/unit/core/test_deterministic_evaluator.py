import pytest
from core.evaluation.plugins.deterministic import DeterministicEvaluator


@pytest.mark.asyncio
async def test_count_assertions():
    evaluator = DeterministicEvaluator()

    # Direct assert (non-constant)
    assert evaluator._count_assertions_python("assert x == 1") == 1

    # Constant assert (should be 0)
    assert evaluator._count_assertions_python("assert 1 == 1") == 0

    # Multiple asserts
    assert evaluator._count_assertions_python("assert x\nassert y") == 2

    # Pytest / Unittest style calls
    test_code = """
import pytest
def test_func(x):
    assert x > 0
    self.assertEqual(x, 1)
    self.assertTrue(x == 1)
    # Use non-constant keyword value to pass anti-theater check
    assert_called_with(val=x)
"""
    # Total = 4
    assert evaluator._count_assertions_python(test_code) == 4


@pytest.mark.asyncio
async def test_find_hollow_methods():
    evaluator = DeterministicEvaluator()

    # 1. 'pass'
    code_pass = "def hollow():\n    pass"
    assert "hollow" in evaluator._find_hollow_methods(code_pass)

    # 2. '...'
    code_ellipsis = "def hollow_dots():\n    ..."
    assert "hollow_dots" in evaluator._find_hollow_methods(code_ellipsis)

    # 3. Identity return
    code_identity = "def identity(x):\n    return x"
    assert "identity" in evaluator._find_hollow_methods(code_identity)

    # 4. Identity return with other args
    code_id_multi = "def first(a, b):\n    return a"
    assert "first" in evaluator._find_hollow_methods(code_id_multi)

    # 5. Non-hollow (logic before return)
    code_logic = "def logic(x):\n    y = x + 1\n    return y"
    assert "logic" not in evaluator._find_hollow_methods(code_logic)


@pytest.mark.asyncio
async def test_deterministic_evaluate_python_scores():
    evaluator = DeterministicEvaluator()

    # Zero assertion case
    res_zero = await evaluator.evaluate("def f(): return 1", "python", test_code="f()")
    assert res_zero.score == 0.0
    assert "CRITICAL" in res_zero.reason

    # Low density case (1 assertion)
    # Must call the function 'f' to avoid theater penalty
    res_low = await evaluator.evaluate("def f(x): return 1", "python", test_code="assert f(1) == 1")
    # 100 - (3-1)*20 = 60
    assert res_low.score == 60.0

    # Hollow logic penalty
    code_hollow = "def hollow(x): pass"
    # Use non-constant assertions and CALL the function
    test_valid = "assert hollow(x) is None\nassert x == 1\nassert y == 2"  # 3 assertions (100)
    res_hollow = await evaluator.evaluate(code_hollow, "python", test_code=test_valid)
    # 100 - 30 = 70
    assert res_hollow.score == 70.0


@pytest.mark.asyncio
async def test_deterministic_skip_non_python():
    evaluator = DeterministicEvaluator()
    # Now requires assertions even for non-python to pass deterministic gate
    # Use 3 assertions to get 100 score
    test_code = "expect(f(1)).toBe(1); expect(f(2)).toBe(2); expect(f(3)).toBe(3);"
    res = await evaluator.evaluate("function f(x) { return x; }", "javascript", test_code=test_code)
    assert res.score == 100.0
    assert "structural pattern matching" in res.reason
