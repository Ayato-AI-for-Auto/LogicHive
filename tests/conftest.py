import hashlib
import importlib
import os
import sqlite3
import sys
import time
import uuid
from unittest.mock import patch

import pytest
from loguru import logger

# --- CRITICAL: SET ENVIRONMENT BEFORE ANY IMPORTS ---
TEST_ROOT = os.path.join(os.getcwd(), ".test_logichive")
os.makedirs(TEST_ROOT, exist_ok=True)

# These will be the default, but individual tests will override SQLITE_DB_PATH
os.environ["SQLITE_DB_PATH"] = os.path.join(TEST_ROOT, "data", "test_logichive.db")
os.environ["FAISS_INDEX_PATH"] = os.path.join(TEST_ROOT, "data", "test_faiss_index.bin")
os.environ["FAISS_MAPPING_PATH"] = os.path.join(TEST_ROOT, "data", "test_faiss_mapping.json")
# os.environ["LOGICHIVE_OFFLINE"] = "true"  # Removed: prevents uv from working correctly


# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# Now safe to import internal modules
import core.config


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        logger.error(f"Test {item.name} failed. Dumping DB metadata...")
        try:
            db_path = os.environ.get("SQLITE_DB_PATH")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                logger.error(f"Current tables: {tables}")
                conn.close()
        except Exception as e:
            logger.error(f"Failed to dump DB metadata: {e}")

class FakeLogicIntelligence:
    def __init__(self, api_key="fake_key"):
        self.api_key = api_key
    async def generate_embedding(self, text: str):
        h = int(hashlib.md5(text.encode()).hexdigest(), 16)
        val = (h % 1000) / 1000.0
        return [val] * 768
    async def evaluate_quality(self, code: str, **kwargs):
        if len(code) < 10 or "break_eval" in code.lower():
            return {"score": 10, "reason": "Fake: Low quality"}
        return {"score": 90, "reason": "Fake: Looks good"}
    async def expand_query(self, query: str):
        return f"TECHNICAL_QUERY: {query}"
    async def rerank_results(self, query: str, results: list, limit: int = 5):
        return results[:limit]
    def construct_search_document(self, name: str, description: str, tags: list, code: str = ""):
        return f"{name} {description} {' '.join(tags)}"
    async def optimize_metadata(self, code: str):
        return {"description": "Automated description", "tags": ["auto"]}
    async def _call_llm_async(self, prompt: str, use_json: bool = False):
        p_lower = prompt.lower()
        if "eval" in p_lower or "exec" in p_lower:
            return {"score": 0, "reason": "Fake: AI Auditor detected risk."}
        if use_json:
            return {
                "name": "fake_func",
                "code": 'def fake_func(): return True',
                "description": "Fake function",
                "tags": ["fake"],
                "dependencies": [],
                "score": 98,
                "reason": "Fake: Verified.",
            }
        return "TECHNICAL_QUERY_EXPANSION"

@pytest.fixture(autouse=True)
def intelligence_isolation(request):
    if "use_real_intelligence" in request.keywords:
        yield
        return
    patches = [
        patch("core.consolidation.LogicIntelligence", new=FakeLogicIntelligence),
        patch("orchestrator.LogicIntelligence", new=FakeLogicIntelligence),
        patch("core.plugins.draft_generator.LogicIntelligence", new=FakeLogicIntelligence),
        patch("core.evaluation.plugins.ai.LogicIntelligence", new=FakeLogicIntelligence),
    ]
    for p in patches: p.start()
    yield
    for p in patches: p.stop()

@pytest.fixture(autouse=True)
async def db_isolation(request):
    """Ensures a fresh, unique environment for every single test."""
    import orchestrator
    import storage.sqlite_api
    from core.db import close_db_connection

    # 1. Setup unique paths
    test_id = uuid.uuid4().hex[:8]
    unique_home = os.path.join(TEST_ROOT, f"home_{test_id}")
    unique_db = os.path.join(unique_home, "data", "test.db")
    os.makedirs(os.path.dirname(unique_db), exist_ok=True)

    # 2. Force environment
    os.environ["LOGICHIVE_HOME"] = unique_home
    os.environ["SQLITE_DB_PATH"] = unique_db

    # 3. Reload config and reset singletons
    importlib.reload(core.config)
    await close_db_connection()
    importlib.reload(storage.sqlite_api)
    importlib.reload(orchestrator)

    yield

    # 4. Cleanup
    await close_db_connection()
    try:
        import shutil
        # Try cleanup but don't fail if Windows locks it
        for _ in range(3):
            try:
                shutil.rmtree(unique_home)
                break
            except: time.sleep(0.1)
    except: pass

@pytest.fixture
async def test_db(db_isolation):
    from storage.init_db import init_db
    await init_db()
    yield

@pytest.fixture(autouse=True)
async def clear_vector_store():
    try:
        import faiss

        from storage.vector_store import vector_manager
        vector_manager.id_to_name = {}
        vector_manager.name_to_id = {}
        vector_manager._current_id = 0
        vector_manager.index = faiss.IndexFlatIP(768)
        vector_manager._initialized = True
    except ImportError: pass
    yield
