# Pure Stateless Orchestrator for LogicHive Hub
import logging
from typing import Any, Dict, List, Optional
from core.quality import QualityGate
from hub.router import router
from core.sanitizer import DataSanitizer

logger = logging.getLogger(__name__)

quality_gate = QualityGate()

def evaluate_candidates(query: str, candidates: List[Dict]) -> Dict:
    """
    Stateless evaluation of search results.
    Receives candidates from Edge and uses hidden logic to select the best one.
    """
    if not candidates:
        return {"status": "error", "message": "No candidates provided."}

    # Use hidden IntelligenceRouter for high-quality matching
    selected_name = router.evaluate_matching(query, candidates)
    
    if not selected_name:
        return {
            "status": "error",
            "message": "No suitable match found among candidates.",
            "candidates": [r.get("name") for r in candidates]
        }

    # Find the full data for the selected candidate
    selected_data = next((c for c in candidates if c.get("name") == selected_name), None)
    
    return {
        "status": "success",
        "selected_function": selected_name,
        "data": selected_data
    }

def validate_function_logic(code: str, context: Dict = {}) -> Dict:
    """
    Stateless quality and security check.
    Returns a report without saving anything.
    """
    from core.security import ASTSecurityChecker, _contains_secrets
    
    # 1. Secret detection
    has_secret, secret_val = _contains_secrets(code)
    if has_secret:
        return {"safe": False, "reason": "Secret detected in code."}

    # 2. Syntax parse
    try:
        import ast
        ast.parse(code)
    except SyntaxError as e:
        return {"safe": False, "reason": f"Syntax Error: {e}"}

    # 3. Security Audit
    is_safe, s_msg = ASTSecurityChecker.check(code)
    if not is_safe:
        return {"safe": False, "reason": f"Security Block: {s_msg}"}

    # 4. Quality Scoring (using hidden weights)
    q_report = quality_gate.check_score_only("temp_asset", code, "", [])
    
    return {
        "safe": True,
        "quality_report": q_report
    }

def sanitize_input(name: str, code: str, description: str, tags: List[str]) -> Dict:
    """Pure stateless sanitization wrapper."""
    return DataSanitizer.sanitize(name, code, description, tags)
