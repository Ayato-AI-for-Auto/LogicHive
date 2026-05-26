import sqlite3

import pytest

from core.evaluation.plugins.static import PythonStaticEvaluator, StructuralEvaluator
from storage.vector_store import VectorIndexManager


@pytest.mark.asyncio
async def test_structural_evaluator_pure():
    """Verifies bracket matching across multiple languages."""
    evaluator = StructuralEvaluator()

    # Python success
    res = await evaluator.evaluate("def test():\n    return (1 + 2)", "python")
    assert res.score == 100.0

    # JS failure (missing closing brace)
    res = await evaluator.evaluate(
        "function test() { if(true) { console.log('hi'); }", "javascript"
    )
    assert res.score == 0.0
    assert "Structural error" in res.reason

    # Harsh test: Deep nesting
    deep_code = "(" * 500 + ")" * 500
    res = await evaluator.evaluate(deep_code, "python")
    assert res.score == 100.0

    # Harsh test: Mismatched types
    res = await evaluator.evaluate("def test(): return [1, 2)", "python")
    assert res.score == 0.0


@pytest.mark.asyncio
async def test_python_static_evaluator_pure():
    """Verifies AST-based checks for Python assets."""
    evaluator = PythonStaticEvaluator()

    # Basic success
    res = await evaluator.evaluate("def single_func(): pass", "python")
    assert res.score == 100.0

    # Multi-function rejection (Atomicity risk)
    res = await evaluator.evaluate("def f1(): pass\ndef f2(): pass", "python")
    assert res.score < 100.0
    assert "Contains 2 functions" in res.reason

    # Syntax Error (Evaluator level)
    res = await evaluator.evaluate("def broken_syntax(:", "python")
    assert res.score == 0.0
    assert "Python Syntax Error" in res.reason


@pytest.mark.asyncio
async def test_vector_store_initialization_filtering(tmp_path):
    """Verifies that VectorIndexManager correctly filters dimensions and 'null' strings."""
    # We use a custom dimension for testing
    manager = VectorIndexManager(dimension=3)
    manager._index_path = str(tmp_path / "test_faiss.bin")
    manager._mapping_path = str(tmp_path / "test_faiss.json")

    dummy_rows = [
        {"name": "valid", "embedding": "[0.1, 0.2, 0.3]", "project": "test"},
        {"name": "wrong_dim", "embedding": "[0.1, 0.2]", "project": "test"},
        {"name": "null_string", "embedding": "null", "project": "test"},
        {"name": "none_val", "embedding": None, "project": "test"},
    ]

    # We don't want it to hit disk, but ensure_initialized handles its own state
    # We pass the rows directly
    await manager.ensure_initialized(dummy_rows)

    # Only 1 should be loaded
    assert manager.index.ntotal == 1
    assert "test:valid" in manager.name_to_id
    assert "test:wrong_dim" not in manager.name_to_id


@pytest.mark.asyncio
async def test_integrity_counting_logic_query(tmp_path):
    """Verifies the specific SQL query used in check_integrity for expected_count."""
    db_path = tmp_path / "test_integrity.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create minimal table
    cursor.execute("""
        CREATE TABLE logichive_functions (
            id TEXT PRIMARY KEY,
            name TEXT,
            embedding TEXT
        )
    """)

    # Insert data simulating various states
    data = [
        ("1", "verified", "[0.1, 0.2]"),
        ("2", "pending", "null"),
        ("3", "failed", None),
        ("4", "verified_2", "[0.3, 0.4]"),
    ]
    cursor.executemany(
        "INSERT INTO logichive_functions (id, name, embedding) VALUES (?, ?, ?)", data
    )
    conn.commit()

    # The query used in check_integrity:
    query = "SELECT COUNT(*) FROM logichive_functions WHERE embedding IS NOT NULL AND embedding != 'null'"
    cursor.execute(query)
    count = cursor.fetchone()[0]

    assert count == 2  # verified and verified_2
    conn.close()
