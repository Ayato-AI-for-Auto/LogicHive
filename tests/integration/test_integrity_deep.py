import asyncio
import os
import sqlite3
import json
import pytest
from storage.sqlite_api import sqlite_storage
from storage.vector_store import vector_manager
from orchestrator import do_save_async, do_search_async

@pytest.mark.asyncio
async def test_deep_data_integrity_handshake(test_db):
    """INTEGRATION: Deep dive into DB and FAISS to ensure physical data integrity."""
    name = "integrity_test"
    code = "def add_logic(a, b):\n    return a + b"
    project = "integrity_deep"

    # 1. Save via Orchestrator
    success = await do_save_async(
        name=name,
        code=code,
        description="Integrity test asset",
        tags=["integrity"],
        project=project,
        test_code="res = add_logic(1, 2)\nassert res == 3",
        dependencies=[]
    )
    assert success is True

    # 2. Wait for background verification (poll)
    max_retries = 10
    verified = False
    status_found = "N/A"
    
    from core.config import SQLITE_DB_PATH
    
    for _ in range(max_retries):
        await asyncio.sleep(0.3)
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT verification_status FROM logichive_functions WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                status_found = row[0]
                if status_found == "verified":
                    verified = True
                    break
        finally:
            conn.close()
    
    if not verified:
        # Get full report for debugging
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT verification_report FROM logichive_functions WHERE name = ?", (name,))
            fail_row = cursor.fetchone()
            pytest.fail(f"Verification failed to reach 'verified' state. Current status: {status_found}. Report: {fail_row[0] if fail_row else 'N/A'}")
        finally:
            conn.close()

    assert verified is True
    
    # 3. VERIFY SQLITE PHYSICALLY (Full check)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM logichive_functions WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    assert row["project"] == project
    assert row["verification_status"] == "verified"
    assert row["env_fingerprint"] is not None
    
    # Check JSON parsing of tags
    tags = json.loads(row["tags"])
    assert "integrity" in tags
    
    # 4. VERIFY FAISS SYNC
    # The vector manager uses 'project:name' as the key
    full_key = f"{project}:{name}"
    assert full_key in vector_manager.name_to_id
    vector_id = vector_manager.name_to_id[full_key]
    
    # Search should find it
    search_results = await do_search_async("nested logic", limit=1, project=project)
    assert len(search_results) > 0
    assert search_results[0]["name"] == name
    
    # 5. VERIFY EMBEDDING COLUMN
    assert row["embedding"] is not None
    emb = json.loads(row["embedding"])
    assert len(emb) == 768 # Default dim
