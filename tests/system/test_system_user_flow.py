import asyncio
import os
import sqlite3
import pytest
from unittest.mock import patch, MagicMock

from core.system.bootstrapper import LogicHiveBootstrapper
from core.exceptions import StorageError
from orchestrator import do_save_async, do_get_verification_status, do_search_async
from storage.sqlite_api import sqlite_storage
from core.db import get_db_connection


@pytest.mark.asyncio
async def test_system_bootstrap_and_user_flow(test_db):
    """System E2E test verifying:
    1. System Bootstrapper environment setup mock.
    2. Registering a function, waiting for verification, and retrieving it via search.
    3. Failure paths by directly injecting database constraints.
    """
    # ==========================================
    # 1. Bootstrapper Setup Environment Simulation
    # ==========================================
    bootstrapper = LogicHiveBootstrapper()
    
    # Assert initially not ready in this clean test_db / home sandbox
    assert bootstrapper.is_venv_ready() is False

    with patch("core.system.bootstrapper.shutil.which", return_value="mock_uv"), \
         patch("core.system.bootstrapper.subprocess.run") as mock_sub_run, \
         patch.object(LogicHiveBootstrapper, "get_venv_python") as mock_get_python:
        
        # Mock python_exe path existence check
        mock_python = MagicMock()
        mock_python.exists.return_value = True
        mock_get_python.return_value = mock_python

        # Execute setup_environment
        success = await bootstrapper.setup_environment()
        assert success is True
        assert mock_sub_run.call_count == 2  # venv creation & dependency pip install

        # After setup, is_venv_ready should evaluate to True
        assert bootstrapper.is_venv_ready() is True

    # ==========================================
    # 2. E2E Function Lifecycle (Register -> Verify -> Search)
    # ==========================================
    project = "calc_proj"
    name = "multiply_numbers"
    code = "def multiply(x, y):\n    return x * y"
    test_code = "assert multiply(3, 4) == 12"

    # Save function
    saved = await do_save_async(
        name=name, code=code, description="multiplies two numbers", test_code=test_code, project=project
    )
    assert saved is True

    # Wait until verified
    for _ in range(20):
        status_data = await do_get_verification_status(name, project=project)
        if status_data["status"] != "pending":
            break
        await asyncio.sleep(0.1)
    
    assert status_data["status"] == "verified"

    # Verify database state directly (情報の裏取り)
    db_path = os.environ["SQLITE_DB_PATH"]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logichive_functions WHERE name = ? AND project = ?", (name, project))
    db_row = cursor.fetchone()
    assert db_row is not None
    assert db_row["verification_status"] == "verified"
    assert db_row["reliability_score"] > 80.0  # Factored from multiple evaluators
    conn.close()

    # Retrieve function via hybrid search
    results = await do_search_async(
        query="multiplies", project=project, limit=1
    )
    assert len(results) == 1
    assert results[0]["name"] == name
    assert results[0]["project"] == project

    # ==========================================
    # 3. DB Failure Path: Inject Integrity / Constraint Violations
    # ==========================================
    # Try to upsert a row violating NOT NULL constraints (e.g. name is Null)
    invalid_data = {
        "project": project,
        "name": None,  # SQLite column 'name' is NOT NULL
        "code": "def bad(): pass",
        "description": "missing name"
    }

    # Verify that SqliteStorage raises StorageError when inserting malformed/violating entries
    with pytest.raises(StorageError):
        await sqlite_storage.upsert_function(invalid_data)

    # Let's perform a raw execution violation directly to verify database raises IntegrityError
    db = await get_db_connection()
    with pytest.raises(sqlite3.IntegrityError):
        await db.execute(
            "INSERT INTO logichive_functions (id, name, code) VALUES (?, ?, ?)",
            ("unique_id_xyz", None, "def error(): pass")
        )
        await db.commit()
