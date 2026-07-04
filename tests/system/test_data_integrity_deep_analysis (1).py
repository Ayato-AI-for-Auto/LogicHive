import json
import sqlite3

import pytest

import core.config
from orchestrator import do_get_verification_status, do_save_async
from storage.vector_store import vector_manager


@pytest.mark.asyncio
async def test_deep_data_analysis(test_db):
    """
    SYSTEM: Deep analysis of stored data.
    Verifies that complex JSON fields in SQLite are valid and accurate.
    """
    name = "analysis_target"
    project = "analysis"
    code = "def logic(a): return a * 2"
    test_code = "assert logic(10) == 20"

    # 1. Register
    await do_save_async(name=name, code=code, test_code=test_code, project=project)

    # 2. Wait for verification
    for _ in range(10):
        status = await do_get_verification_status(name, project=project)
        if status["status"] == "verified":
            break
        import asyncio
        await asyncio.sleep(0.5)

    # 3. Direct SQLite Analysis
    conn = sqlite3.connect(core.config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logichive_functions WHERE name=?", (name,))
    row = cursor.fetchone()
    conn.close()

    print("\n--- Physical Data Analysis ---")

    # Verify Reliability Score is a float
    assert isinstance(row["reliability_score"], float)
    print(f"Score: {row['reliability_score']}")

    # Verify verification_report is valid JSON
    report = json.loads(row["verification_report"])
    assert "details" in report
    assert "runtime" in report["details"]
    print(f"Report keys: {list(report['details'].keys())}")

    # Verify test_metrics is valid JSON
    metrics = json.loads(row["test_metrics"])
    assert isinstance(metrics, dict)
    print(f"Metrics: {metrics}")

    # Verify Environment Fingerprint
    assert row["env_fingerprint"] is not None
    env = json.loads(row["env_fingerprint"])
    assert "os" in env
    print(f"Env: {env['os']} ({env.get('python_version')})")

@pytest.mark.asyncio
async def test_zombie_detection(test_db):
    """
    SYSTEM: Check for synchronization between DB and FAISS.
    """
    # Force a desync by inserting directly via SQL (bypassing the logic that updates FAISS)
    conn = sqlite3.connect(core.config.SQLITE_DB_PATH)
    conn.execute(
        "INSERT INTO logichive_functions (id, name, project, code, embedding) VALUES (?, ?, ?, ?, ?)",
        ("ghost-id", "ghost", "default", "pass", json.dumps([0.1]*768))
    )
    conn.commit()
    conn.close()

    # The record exists in DB with embedding, but vector_manager doesn't know it yet
    # (Unless it was just reloaded)

    # Analysis: Count verified assets in DB
    conn = sqlite3.connect(core.config.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM logichive_functions WHERE embedding IS NOT NULL")
    db_count = cursor.fetchone()[0]
    conn.close()

    # Count in FAISS
    faiss_count = len(vector_manager.id_to_name)

    print("\n--- Sync Analysis ---")
    print(f"DB Assets with Embeddings: {db_count}")
    print(f"FAISS Memory Assets: {faiss_count}")

    # In a healthy system they should match (if initialized)
    # But here we expect a mismatch because we bypassed the orchestrator
    assert db_count == 1
    assert faiss_count == 0

    # Trigger self-healing (rebuild)
    await vector_manager.rebuild_index()
    assert len(vector_manager.id_to_name) == 1
    print("Self-healing (Rebuild) successful.")
