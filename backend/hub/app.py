import logging
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional

from core.config import HOST, PORT

logger = logging.getLogger("hub_app")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="LogicHive Hub: Pure Stateless Logic Engine")

# --- DATA MODELS ---

class VerifyRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None

class VerifyFinalizeRequest(BaseModel):
    name: str
    code: str
    llm_output: str
    description: Optional[str] = None
    dependencies: Optional[List[str]] = None

class RerankRequest(BaseModel):
    query: str
    candidates: List[Dict]

class RerankFinalizeRequest(BaseModel):
    candidates: List[Dict]
    llm_output: str

class PushRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    metadata: Optional[Dict] = None

# --- ENDPOINTS ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": "pure-stateless"}

# --- INTELLIGENCE ENDPOINTS (Stateless Evaluation) ---

@app.post("/api/v1/intelligence/verify/get-prompt")
async def intelligence_verify_get_prompt(req: VerifyRequest):
    """
    Step 1: Hub generates the quality check prompt for the client.
    Does NOT save the code.
    """
    logger.info(f"Hub: Generating verification prompt for '{req.name}'")
    from core.quality import QualityGate
    q_gate = QualityGate()
    prompt = q_gate.get_verification_prompt(
        req.name, req.code, req.description or ""
    )
    return {"prompt": prompt}

@app.post("/api/v1/intelligence/verify/finalize")
async def intelligence_verify_finalize(req: VerifyFinalizeRequest):
    """
    Step 2: Hub combines static analysis with client's LLM feedback.
    Returns a reliability report to be saved by the Edge.
    """
    logger.info(f"Hub: Finalizing verification for '{req.name}'")
    from core.quality import QualityGate
    q_gate = QualityGate()
    result = q_gate.finalize_verification(
        req.name, req.code, req.llm_output, req.description or "", req.dependencies
    )
    return result

@app.post("/api/v1/intelligence/rerank/get-prompt")
async def intelligence_rerank_get_prompt(req: RerankRequest):
    """
    Step 1: Hub generates the secret rerank prompt for the client.
    """
    logger.info(f"Hub: Generating rerank prompt for query '{req.query}'")
    from hub.router import router
    prompt = router.get_prompt(req.query, req.candidates)
    return {"prompt": prompt}

@app.post("/api/v1/intelligence/rerank/finalize")
async def intelligence_rerank_finalize(req: RerankFinalizeRequest):
    """
    Step 2: Hub parses the client-provided LLM result to determine the winner.
    """
    logger.info("Hub: Finalizing rerank decision.")
    from hub.router import router
    selected_name = router.finalize_decision(req.candidates, req.llm_output)
    return {"selected_name": selected_name}

@app.post("/api/v1/sync/push")
async def sync_push(req: PushRequest):
    """
    Mediated Push: Hub receives function data and pushes to GitHub Storage.
    Only called by Edge client after validation.
    """
    logger.info(f"Hub: Mediated push request for '{req.name}'")
    from hub.github_api import push_function_to_github
    success, message = push_function_to_github(
        name=req.name,
        code=req.code,
        description=req.description or "",
        tags=req.tags or [],
        dependencies=req.dependencies or [],
        metadata=req.metadata or {}
    )
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to push: {message}")
    
    return {"status": "success", "message": f"Function '{req.name}' pushed to storage."}

if __name__ == "__main__":
    logger.info(f"LogicHive Hub starting (Stateless) on {HOST}:{PORT}...")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
