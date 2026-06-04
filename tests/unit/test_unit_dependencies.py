import textwrap

from orchestrator import extract_dependencies


def test_extract_dependencies_python_simple():
    code = "import os\nimport requests\nfrom datetime import datetime"
    deps = extract_dependencies(code, language="python")
    # os and datetime are stdlib, requests is external
    assert "requests" in deps
    assert "os" not in deps
    assert "datetime" not in deps

def test_extract_dependencies_python_complex():
    code = textwrap.dedent("""
        import numpy as np
        from sklearn.linear_model import LinearRegression
        import torch.nn as nn
    """)
    deps = extract_dependencies(code, language="python")
    assert "numpy" in deps
    assert "sklearn" in deps
    assert "torch" in deps

def test_extract_dependencies_js():
    code = """
    import axios from 'axios';
    const express = require('express');
    const path = require('./path');
    """
    deps = extract_dependencies(code, language="javascript")
    assert "axios" in deps
    assert "express" in deps
    assert "./path" not in deps

def test_extract_dependencies_empty():
    assert extract_dependencies("", language="python") == []
    assert extract_dependencies("print('hello')", language="python") == []

def test_extract_dependencies_malformed():
    # Should not crash on invalid syntax
    code = "import !!! invalid"
    deps = extract_dependencies(code, language="python")
    assert isinstance(deps, list)
