import pytest
import textwrap
import random
import string
from core.evaluation.manager import EvaluationManager

@pytest.mark.asyncio
async def test_chaos_complexity_ceiling():
    """
    Chaos: Generate a function with extreme cyclomatic complexity (100 nested ifs).
    Verify that Radon handles it without crashing and assigns a low maintainability score.
    """
    manager = EvaluationManager()
    
    # Generate 100 nested if statements
    code = "def complex_func(x):\n"
    for i in range(100):
        code += f"{'    ' * (i+1)}if x == {i}:\n"
    code += f"{'    ' * 101}return {random.randint(0, 1000)}\n"
    for i in range(100, 0, -1):
        code += f"{'    ' * i}else:\n{'    ' * (i+1)}pass\n"
    code += "    return -1"

    results = await manager.evaluate_all(code=code, language="python", test_code="assert complex_func(1) != 0")
    
    metrics_res = results["details"].get("metrics_gate")
    if metrics_res:
        # Should be penalized for extreme complexity
        assert metrics_res["score"] < 50
        print(f"DEBUG: Complexity Score: {metrics_res['score']}, Reason: {metrics_res['reason']}")

@pytest.mark.asyncio
async def test_chaos_giant_payload_stability():
    """
    Chaos: Send a 10,000 line Python file to the quality gate.
    Ensures that static analysis tools (Ruff/AST) handle it or time out gracefully.
    """
    manager = EvaluationManager()
    
    # Generate 10k lines of dummy methods
    lines = ["def func_{}(x): return x + {}".format(i, i) for i in range(10000)]
    code = "\n".join(lines)
    test_code = "assert func_0(1) == 1"

    # We expect this to finish or hit a system timeout, but NOT crash the process
    results = await manager.evaluate_all(code=code, language="python", test_code=test_code)
    
    assert "details" in results
    print(f"DEBUG: Giant payload processed. Status: {results['score']}")

@pytest.mark.asyncio
async def test_chaos_assertion_flooding_quality_theater():
    """
    Chaos: 
    1. Provide 1,000 trivial assertions (assert 1==1). Should yield 0 score.
    2. Provide nested dynamic assertions. Should yield high score.
    """
    manager = EvaluationManager()
    code = "def add(a, b): return a + b"
    
    # CASE 1: 1000 trivial asserts (Quality Theater)
    test_code_theater = "def test():\n" + "\n".join(["    assert 1 == 1"] * 1000) + "\ntest()"
    res_theater = await manager.evaluate_all(code=code, language="python", test_code=test_code_theater)
    assert res_theater["details"]["deterministic"]["details"]["assertion_count"] == 0
    print(f"DEBUG: Theater Score: {res_theater['details']['deterministic']['score']} (Expected: 0.0)")

    # CASE 2: Nested dynamic asserts (Real Testing)
    test_code_real = textwrap.dedent("""
        def test_add():
            x = 1
            assert add(x, 1) == 2
            assert add(x, 2) == 3
            assert add(x, 3) == 4
        test_add()
    """)
    res_real = await manager.evaluate_all(code=code, language="python", test_code=test_code_real)
    # Should count 3 assertions even though they are inside a function
    assert res_real["details"]["deterministic"]["details"]["assertion_count"] == 3
    print(f"DEBUG: Real Nested Score: {res_real['details']['deterministic']['score']} (Expected: 100.0)")

@pytest.mark.asyncio
async def test_chaos_binary_data_resilience():
    """
    Chaos: Supply raw binary data as 'python' code.
    Verify that the system treats it as a syntax error or invalid encoding without crashing.
    """
    manager = EvaluationManager()
    
    # Raw non-UTF8 binary data
    code = b"\x80\x81\xff\xfe\x00\x01".decode("latin-1") 
    test_code = "assert True"

    results = await manager.evaluate_all(code=code, language="python", test_code=test_code)
    
    # Static gate or structural gate should catch this
    assert results["score"] < 50
    print(f"DEBUG: Binary data score: {results['score']}, Reason: {results.get('reason', 'N/A')}")
