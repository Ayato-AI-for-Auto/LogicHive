import sqlite3
import pytest
from storage.sqlite_api import sqlite_storage
from storage.vector_store import vector_manager
import core.config

@pytest.mark.asyncio
async def test_storage_upsert_and_physical_check(test_db):
    """
    INTEGRATION: Verify that upsert_function actually writes correct data to SQLite.
    We check the 'physical' state by opening a direct sqlite3 connection.
    """
    name = "test_func"
    data = {
        "id": "123",
        "name": name,
        "project": "default",
        "code": "def test_func(): pass",
        "language": "python",
        "reliability_score": 0.85,
        "verification_status": "verified"
    }
    
    # 1. LogicHive API call
    await sqlite_storage.upsert_function(data)
    
    # 2. Physical verification (Direct SQL)
    conn = sqlite3.connect(core.config.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, reliability_score, verification_status FROM logichive_functions WHERE name=?", (name,))
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    assert row[0] == name
    assert row[1] == 0.85
    assert row[2] == "verified"

@pytest.mark.asyncio
async def test_storage_vector_sync(test_db):
    """
    INTEGRATION: Verify that adding an embedding updates both DB and FAISS index.
    """
    name = "vector_test"
    project = "default"
    embedding = [0.1] * 768
    
    # Pre-condition: Create record
    await sqlite_storage.upsert_function({"name": name, "project": project, "code": "..."})
    
    # 1. Update embedding via storage
    await sqlite_storage.update_function_embedding(name, project, embedding)
    
    # 2. Update FAISS via vector_manager
    await vector_manager.upsert_vector(name, embedding, metadata={"project": project}, project=project)
    
    # 3. Verify DB physical state
    conn = sqlite3.connect(core.config.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT embedding FROM logichive_functions WHERE name=?", (name,))
    row = cursor.fetchone()
    conn.close()
    
    assert row[0] is not None  # JSON string in DB
    
    # 4. Verify FAISS state
    assert vector_manager.index.ntotal == 1
    assert f"{project}:{name}" in vector_manager.name_to_id

@pytest.mark.asyncio
async def test_storage_deletion_integrity(test_db):
    """
    INTEGRATION: Verify that deleting a function removes it from both SQLite and FAISS.
    """
    name = "delete_me"
    project = "default"
    embedding = [0.5] * 768
    
    await sqlite_storage.upsert_function({"name": name, "project": project, "code": "..."})
    await vector_manager.upsert_vector(name, embedding, metadata={"project": project}, project=project)
    
    # 1. Perform deletion
    await sqlite_storage.delete_function(name, project=project)
    await vector_manager.remove_vector(name, project=project)
    
    # 2. Verify DB is empty
    conn = sqlite3.connect(core.config.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM logichive_functions WHERE name=?", (name,))
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 0
    
    # 3. Verify FAISS is updated (soft delete or removal)
    # Note: Our FAISS implementation might use mapping deletion
    assert name not in vector_manager.name_to_id
