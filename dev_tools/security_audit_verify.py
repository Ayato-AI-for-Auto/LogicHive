import os
import json
import logging
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Base directory is the repository root
repo_root = Path(__file__).parent.parent
backend_dir = repo_root / "backend"

# Add backend directory to sys.path
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

# Mocking environment for DuckDB to use a temporary location
os.environ["FS_DB_NAME"] = "test_audit.duckdb"
os.environ["FS_SYNC_LOCAL_DIR"] = str(repo_root / "data" / "test_hub_cache")

from edge.sync import GitHubSyncEngine
from core.database import init_db

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

def test_security_audit():
    print("\n--- LogicHive Zero-Key Transmission Audit ---")
    
    # 1. Setup Mock environment with a "Secret API Key"
    secret_key = "sk-logic-hive-PROVEN-SECRET-DO-NOT-SEND"
    os.environ["FS_GEMINI_API_KEY"] = secret_key
    
    # 2. Prepare mock data in DuckDB
    init_db()
    from core.database import get_db_connection
    conn = get_db_connection()
    conn.execute("DELETE FROM functions WHERE name = 'audit_test_func'")
    conn.execute(
        "INSERT INTO functions (name, code, description, status) VALUES (?, ?, ?, ?)",
        ("audit_test_func", "print('hello')", "Audit Test", "verified")
    )
    conn.commit()
    conn.close()
    
    # 3. Patch both Git and httpx
    with patch("git.Repo") as mock_repo_class, \
         patch("httpx.Client.post") as mock_post:
        
        # Mock Git
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo_class.clone_from.return_value = mock_repo
        
        # Mock successful Hub response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response
        
        sync = GitHubSyncEngine()
        # Pretend repo exists locally
        (Path(os.environ["FS_SYNC_LOCAL_DIR"]) / ".git").mkdir(parents=True, exist_ok=True)
        
        print("[AUDIT] Triggering push to Hub...")
        sync.push("audit_test_func")
        
        # 4. Verify the capture
        if mock_post.called:
            args, kwargs = mock_post.call_args
            url = args[0]
            payload = kwargs.get("json", {})
            
            print(f"[AUDIT] Captured POST to: {url}")
            payload_str = json.dumps(payload)
            
            # Check for the secret key in ANY field
            if secret_key in payload_str or secret_key in str(kwargs.get("headers", {})):
                print("[FAILURE] 🚨 SECURITY BREACH: Secret API Key found in outgoing payload!")
                exit(1)
            else:
                print("[SUCCESS] ✅ CLEAN: No API Key found in communication payload.")
                print(f"[AUDIT] Fields sent: {list(payload.keys())}")
        else:
            print("[ERROR] Push operation was not called. Check if ensure_repo() passed.")
            exit(1)

    print("--- Audit Finished ---\n")

if __name__ == "__main__":
    test_security_audit()
