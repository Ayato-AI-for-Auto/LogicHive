import pytest
from core.system_info import SystemFingerprint

def test_fingerprint_generation():
    """UNIT: Verify that system fingerprint contains required platform keys."""
    fp = SystemFingerprint.get_current()
    assert "os" in fp
    assert "python_version" in fp
    assert "cpu_arch" in fp
    assert "execution_driver" in fp

def test_fingerprint_comparison_no_diff():
    """UNIT: Verify that identical fingerprints result in no differences."""
    fp = {
        "os": "Windows",
        "python_version": "3.11.3",
        "cpu_arch": "AMD64",
        "execution_driver": "venv"
    }
    diffs = SystemFingerprint.compare(fp, fp)
    assert len(diffs) == 0

def test_fingerprint_comparison_with_diffs():
    """UNIT: Verify that significant differences are detected."""
    fp1 = {
        "os": "Windows",
        "python_version": "3.11.3",
        "cpu_arch": "AMD64",
        "execution_driver": "venv"
    }
    fp2 = {
        "os": "Linux",
        "python_version": "3.12.0",
        "cpu_arch": "arm64",
        "execution_driver": "docker"
    }
    diffs = SystemFingerprint.compare(fp1, fp2)
    assert len(diffs) >= 4
    assert any("OS mismatch" in d for d in diffs)
    assert any("Python Version Drift" in d for d in diffs)
    assert any("Architecture Drift" in d for d in diffs)
    assert any("Execution Driver Change" in d for d in diffs)
