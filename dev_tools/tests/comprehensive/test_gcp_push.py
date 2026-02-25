import os
import json
from edge.sync import GitHubSyncEngine
from core import config
import httpx

# Configuration for Live Test
LIVE_HUB_URL = "https://function-store-hub-wqrdbid6cq-an.a.run.app"
TEST_FUNC_NAME = "gcp_live_verification_test"

def test_live_push():
    print(f"--- Starting Comprehensive Test on Live Hub: {LIVE_HUB_URL} ---")
    
    # 1. Override Hub URL
    config.HUB_URL = LIVE_HUB_URL
    
    # 2. Setup Engine with Temporary Paths
    import tempfile
    from pathlib import Path
    temp_dir = Path(tempfile.mkdtemp())
    engine = GitHubSyncEngine()
    engine.local_dir = temp_dir
    engine.functions_dir = temp_dir / "functions"
    engine.functions_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock ensure_repo to skip actual git operations
    import unittest.mock as mock
    engine.ensure_repo = mock.MagicMock(return_value=True)

    # 3. Create a dummy function file
    data = {
        "name": TEST_FUNC_NAME,
        "code": "def hello_gcp():\n    return 'Success from Live Hub!'",
        "description": "Verification function for Stage 3 GCP Deployment.",
        "tags": ["gcp", "test", "verification"],
        "dependencies": [],
        "quality_score": 100
    }
    
    fpath = engine.functions_dir / f"{TEST_FUNC_NAME}.json"
    print(f"Writing test file to {fpath}")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # 4. Trigger Push (Direct HTTPX for better diagnostics)
    print(f"Triggering direct POST to Hub...")
    url = f"{config.HUB_URL}/api/v1/sync/push"
    try:
        resp = httpx.post(url, json=data, timeout=30.0)
        print(f"Status Code: {resp.status_code}")
        print(f"Response Body: {resp.text}")
        success = (resp.status_code == 200)
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        success = False
    
    return success
    
if __name__ == "__main__":
    test_live_push()
