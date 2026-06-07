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


@pytest.mark.asyncio
async def test_dependency_vouch_vulnerabilities():
    """UNIT: Verify that DependencyVouchEvaluator flags known vulnerable packages."""
    from core.evaluation.plugins.dependency_vouch import DependencyVouchEvaluator

    evaluator = DependencyVouchEvaluator()
    code = "import urllib3\ndef get(): pass"

    # We pass a known vulnerable version "urllib3==1.26.15" via dependencies
    res = await evaluator.evaluate(code, language="python", dependencies=["urllib3==1.26.15"])

    assert res.score < 100.0
    assert "Security vulnerabilities detected" in res.reason
    assert len(res.details.get("vulnerabilities", [])) > 0


@pytest.mark.asyncio
async def test_periodic_vulnerability_scan_loop(test_db):
    """UNIT: Verify that the background periodic scan loop updates function scores in DB."""
    import asyncio
    from unittest.mock import patch

    from mcp_server import _periodic_vulnerability_scan_loop
    from storage.sqlite_api import sqlite_storage

    # Insert a function with vulnerable dependency "urllib3==1.26.15"
    await sqlite_storage.upsert_function({
        "name": "func_to_scan",
        "code": "import urllib3",
        "description": "test",
        "tags": [],
        "language": "python",
        "reliability_score": 100.0,
        "embedding": [0.1] * 768,
        "project": "default",
        "verification_status": "verified",
        "dependencies": ["urllib3==1.26.15"],
    })

    # We mock asyncio.sleep so that the first call allows execution but then cancels/raises to break the loop
    sleep_count = 0
    original_sleep = asyncio.sleep

    async def mock_sleep(delay, result=None):
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count > 1:  # Break the loop on the 24 hour sleep
            raise asyncio.CancelledError()
        await original_sleep(0.01)

    with patch("asyncio.sleep", side_effect=mock_sleep):
        try:
            await _periodic_vulnerability_scan_loop()
        except asyncio.CancelledError:
            pass

    # Verify that the function in the DB has its score reduced and status updated to 'failed'
    updated = await sqlite_storage.get_function_by_name("func_to_scan")
    assert updated is not None
    assert updated["verification_status"] == "failed"
    assert updated["reliability_score"] < 100.0
    report = updated.get("verification_report") or {}
    vulns = report.get("details", {}).get("dependency_vouch", {}).get("details", {}).get("vulnerabilities", [])
    assert len(vulns) > 0
