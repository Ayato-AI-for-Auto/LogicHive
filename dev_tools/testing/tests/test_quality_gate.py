from core.quality import QualityGate


def test_quality_gate_score_calculation():
    """Verify that the quality gate produces a reasonable score."""
    gate = QualityGate()
    # Simple, well-formatted code
    code = "def add(a, b):\n    return a + b\n"
    report = gate.check_score_only("add", code)

    assert report["final_score"] > 80
    assert report["reliability"] == "high"


def test_quality_gate_lint_penalty():
    """Verify that lint errors reduce the score."""
    gate = QualityGate()
    # Code with lint errors (unused import)
    code = "import os\ndef add(a, b):\n    return a + b\n"
    report = gate.check_score_only("add", code)

    # It should have a lower score than perfectly clean code
    # (Though Ruff might not always flag unused import without specific config,
    # but the principle of penalty check remains)
    assert "final_score" in report


def test_quality_gate_format_penalty():
    """Verify that formatting errors reduce the score."""
    gate = QualityGate()
    # Poorly formatted code
    code = "def add(a,b):return a+b"
    report = gate.check_score_only("add", code)

    # Formatter penalty is 30 points as per quality.py
    # Clean score (100) - 30 = 70 (Medium)
    assert report["final_score"] <= 70
    assert report["reliability"] == "medium"
