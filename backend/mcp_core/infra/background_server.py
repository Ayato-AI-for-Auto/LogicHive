import logging
import os
import sys
import threading
import time
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Ensure mcp_core is importable
# In a real environment, the PYTHONPATH should be set correctly,
# but we add this for robustness when run via sys.executable -m
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root not in sys.path:
    sys.path.insert(0, root)

from mcp_core.core.config import HOST, PORT  # noqa: E402
from mcp_core.core.database import _check_model_version, init_db  # noqa: E402
from mcp_core.engine.cleanup import run_forget_cleanup  # noqa: E402
from mcp_core.engine.logic import (  # noqa: E402
    do_archive_impl,
    do_delete_impl,
    do_get_details_impl,
    do_get_impl,
    do_inject_impl,
    do_list_impl,
    do_restore_impl,
    do_save_impl,
    do_search_impl,
    do_smart_get_impl,
    do_triage_list_impl,
)
from mcp_core.engine.worker import task_worker  # noqa: E402

# Re-use coordinator port
MASTER_PORT = PORT + 100

logger = logging.getLogger("background_server")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Function Store Master Service")


class ToolRequest(BaseModel):
    tool: str
    arguments: dict


class SaveRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    test_cases: Optional[List[Dict]] = None
    skip_test: bool = False


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class SmartSearchRequest(BaseModel):
    query: str
    target_dir: Optional[str] = None


class ListRequest(BaseModel):
    query: Optional[str] = None
    tag: Optional[str] = None
    limit: int = 100
    include_archived: bool = False


class VerifyRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    test_cases: Optional[List[Dict]] = None


class RerankRequest(BaseModel):
    query: str
    candidates: List[Dict]


# Idle Shutdown Logic
last_request_time = time.time()
IDLE_TIMEOUT = 1800  # 30 minutes


def idle_checker():
    global last_request_time
    while True:
        if time.time() - last_request_time > IDLE_TIMEOUT:
            logger.info(f"Idle for {IDLE_TIMEOUT}s. Shutting down Master process.")
            os._exit(0)
        time.sleep(60)


threading.Thread(target=idle_checker, daemon=True).start()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/execute")
async def execute_tool(req: ToolRequest):
    """Legacy endpoint for proxy routing."""
    global last_request_time
    last_request_time = time.time()

    logger.info(f"Master: Executing {req.tool}...")
    try:
        # Dynamic dispatch (mapping tool names to implementations)
        handlers = {
            "save_function": do_save_impl,
            "search_functions": do_search_impl,
            "get_function_details": do_get_details_impl,
            "delete_function": do_delete_impl,
            "list_functions": do_list_impl,
            "get_function": do_get_impl,
            "inject_local_package": do_inject_impl,
            "smart_search_and_get": do_smart_get_impl,
            "get_triage_list": do_triage_list_impl,
            "archive_function": do_archive_impl,
            "restore_function": do_restore_impl,
        }

        if req.tool in handlers:
            res = handlers[req.tool](**req.arguments)
            return {"result": res}
        else:
            return {"error": f"Unknown tool: {req.tool}"}
    except Exception as e:
        logger.error(f"Master: Tool execution error: {e}")
        return {"error": str(e)}


# --- NEW RESTFUL ENDPOINTS ---


@app.get("/api/v1/functions")
async def list_functions(
    query: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100,
    include_archived: bool = False,
):
    global last_request_time
    last_request_time = time.time()
    return {
        "result": do_list_impl(
            query=query, tag=tag, limit=limit, include_archived=include_archived
        )
    }


@app.post("/api/v1/functions")
async def save_function(req: SaveRequest):
    global last_request_time
    last_request_time = time.time()
    return {
        "result": do_save_impl(
            asset_name=req.name,
            code=req.code,
            description=req.description,
            tags=req.tags,
            dependencies=req.dependencies,
            test_cases=req.test_cases,
            skip_test=req.skip_test,
        )
    }


@app.get("/api/v1/functions/{name}")
async def get_function_details(name: str):
    global last_request_time
    last_request_time = time.time()
    res = do_get_details_impl(name)
    if not res:
        raise HTTPException(status_code=404, detail="Function not found")
    return {"result": res}


@app.get("/api/v1/functions/{name}/code")
async def get_function_code(name: str):
    global last_request_time
    last_request_time = time.time()
    return {"result": do_get_impl(name)}


@app.delete("/api/v1/functions/{name}")
async def delete_function(name: str):
    global last_request_time
    last_request_time = time.time()
    return {"result": do_delete_impl(name)}


@app.post("/api/v1/search")
async def search_functions(req: SearchRequest):
    global last_request_time
    last_request_time = time.time()
    return {"result": do_search_impl(query=req.query, limit=req.limit)}


@app.post("/api/v1/smart-search")
async def smart_search(req: SmartSearchRequest):
    global last_request_time
    last_request_time = time.time()
    return {"result": do_smart_get_impl(query=req.query, target_dir=req.target_dir)}


@app.get("/api/v1/triage")
async def get_triage(limit: int = 5):
    global last_request_time
    last_request_time = time.time()
    return {"result": do_triage_list_impl(limit=limit)}


@app.post("/api/v1/functions/{name}/archive")
async def archive_function(name: str):
    global last_request_time
    last_request_time = time.time()
    return {"result": do_archive_impl(name)}


@app.post("/api/v1/functions/{name}/restore")
async def restore_function(name: str):
    global last_request_time
    last_request_time = time.time()
    return {"result": do_restore_impl(name)}


# --- INTELLIGENCE ENDPOINTS (Hybrid Logic) ---


@app.post("/api/v1/intelligence/verify")
async def intelligence_verify(req: VerifyRequest):
    """
    Performs high-level intelligence verification (Quality Gate, Dependency Analysis)
    without necessarily committing to a local persistent store.
    """
    global last_request_time
    last_request_time = time.time()
    logger.info(f"Intelligence: Verifying '{req.name}'...")

    from mcp_core.engine.dependency_solver import DependencySolver
    from mcp_core.engine.quality_gate import QualityGate

    q_gate = QualityGate()
    # Quality Scoring
    q_report = q_gate.check_score_only(
        req.name, req.code, req.description, req.dependencies or []
    )

    # Dependency Analysis
    detected_deps = DependencySolver.extract_imports(req.code)

    return {
        "status": q_report.get("reliability", "low"),
        "metadata": {
            "quality_score": q_report.get("final_score", 0),
            "reliability_tier": q_report.get("reliability", "low"),
            "detected_imports": detected_deps,
            "quality_feedback": q_report.get("feedback", ""),
        },
    }


@app.post("/api/v1/intelligence/rerank")
async def intelligence_rerank(req: RerankRequest):
    """
    AI-based reranking of candidates provided by the Edge DB.
    """
    global last_request_time
    last_request_time = time.time()
    logger.info(
        f"Intelligence: Reranking {len(req.candidates)} candidates for query '{req.query}'"
    )

    from mcp_core.engine.router import router

    selected_name = router.evaluate_matching(req.query, req.candidates)
    return {"selected_name": selected_name}


if __name__ == "__main__":
    init_db()
    _check_model_version()
    # Auto-cleanup on startup (Background)
    task_worker.add_task(run_forget_cleanup)
    logger.info(f"Master starting on {HOST}:{MASTER_PORT}...")
    uvicorn.run(app, host=HOST, port=MASTER_PORT, log_level="info")
