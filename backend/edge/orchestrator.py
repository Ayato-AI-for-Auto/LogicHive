import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Set

from core.database import DBWriteLock, get_db_connection
from edge.vector_db import get_vector_db
from core.embedding import embedding_service
from edge.cache import PopularQueryCache
from core.quality import QualityGate
from core.sanitizer import DataSanitizer
from edge.worker import task_worker
import httpx

logger = logging.getLogger(__name__)

HUB_URL = os.getenv(
    "LOGICHIVE_HUB_URL", "https://function-store-hub-wqrdbid6cq-an.a.run.app"
)

quality_gate = QualityGate()
popular_cache = PopularQueryCache()


def _record_usage(name: str):
    """Internal helper to track function usage in DuckDB."""
    with DBWriteLock():
        conn = get_db_connection()
        try:
            now = datetime.now().isoformat()
            conn.execute(
                "UPDATE functions SET call_count = call_count + 1, last_called_at = ?, updated_at = ? WHERE name = ?",
                (now, now, name),
            )
            conn.commit()
        finally:
            conn.close()


def do_save_impl(
    asset_name: str,
    code: str,
    description: str = "",
    tags: List[str] = [],
    dependencies: List[str] = [],
    test_cases: List[Dict] = [],
    skip_test: bool = False,
) -> str:
    """Stateful saving to local DuckDB and VectorDB."""
    if not description.strip():
        now_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        description = f"Draft automatically saved by AI on {now_date}"

    sanitized = DataSanitizer.sanitize(asset_name, code, description, tags)
    asset_name, code, description, tags = (
        sanitized["name"],
        sanitized["code"],
        sanitized["description"],
        sanitized["tags"],
    )

    with DBWriteLock():
        conn = get_db_connection()
        try:
            is_syntax_valid = True
            try:
                import ast

                ast.parse(code)
            except SyntaxError:
                is_syntax_valid = False

            from core.security import _contains_secrets

            has_secret, _ = _contains_secrets(code)
            if has_secret:
                return "REJECTED: Secret detected in code."

            initial_status = "pending" if is_syntax_valid else "broken"
            now = datetime.now().isoformat()

            metadata = {
                "dependencies": dependencies,
                "saved_at": now,
                "quality_score": 0 if not is_syntax_valid else 50,
            }

            conn.execute(
                """
                INSERT OR REPLACE INTO functions (name, code, description, tags, metadata, test_cases, status, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    asset_name,
                    code,
                    description,
                    json.dumps(tags),
                    json.dumps(metadata),
                    json.dumps(test_cases),
                    initial_status,
                    now,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    task_worker.add_task(
        run_background_maintenance,
        asset_name,
        code,
        description,
        tags,
        dependencies,
        test_cases,
        skip_test,
    )
    return f"SUCCESS: '{asset_name}' saved locally. Background verification started."


def run_background_maintenance(
    f_name, f_code, f_desc, f_tags, f_deps, f_tests, skip_verify
):
    """Local indexing + background tasks (Test Execution)."""
    try:
        # 1. Vector Database Indexing
        txt = f"Name: {f_name}\nDesc: {f_desc}\nTags: {f_tags}\nCode:\n{f_code[:500]}"
        emb = embedding_service.get_embedding(txt)
        v_list = emb.tolist()
        get_vector_db().upsert_function(f_name, v_list, {"name": f_name})

        # 2. Test Execution (Phase 2: Verified-First Enforcement)
        status = "verified"
        if f_tests and not skip_verify:
            logger.info(f"Running verification tests for '{f_name}'...")
            try:
                # Assuming main.py is running on 8080 locally for verification
                exec_url = "http://localhost:8080/execute" 
                # Note: In a real deploy, orchestration might point to a specific internal URL
                
                with httpx.Client(timeout=35.0) as client:
                    resp = client.post(
                        exec_url,
                        json={"code": f_code, "test_cases": f_tests},
                        headers={"X-API-Key": "PRO-MOCK-KEY-123"} # Mock key for local verification
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "success":
                            logger.info(f"Tests passed for '{f_name}'.")
                            status = "verified"
                        else:
                            logger.warning(f"Tests failed for '{f_name}': {data.get('error')}")
                            status = "failed"
                    else:
                        logger.error(f"Execution server error ({resp.status_code}) for '{f_name}'")
                        status = "error_internal"
            except Exception as e:
                logger.error(f"Failed to call execution server: {e}")
                status = "error_internal"
        elif not f_tests and not skip_verify:
            # If no tests provided, we can't fully "verify" in the new policy, but let's mark as pending_tests
            status = "pending_tests"

        # 3. Update DuckDB Status
        with DBWriteLock():
            conn = get_db_connection()
            try:
                conn.execute(
                    "UPDATE functions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE name = ?",
                    (status, f_name),
                )
                conn.commit()
            finally:
                conn.close()
                
    except Exception as e:
        logger.error(f"Background Maintenance Error for '{f_name}': {e}")


def do_search_impl(query: str, limit: int = 5) -> List[Dict]:
    """Pure local search with 'Verified' boosting."""
    emb = embedding_service.get_embedding(query).tolist()
    search_results = get_vector_db().search(emb, limit=limit)

    results = []
    conn = get_db_connection()
    try:
        for point in search_results:
            p = point.payload
            name = p.get("name")
            
            # Fetch status for badge/boosting
            row = conn.execute("SELECT status FROM functions WHERE name = ?", (name,)).fetchone()
            status = row[0] if row else "unknown"
            
            # Boost score if verified
            score = float(point.score)
            if status == "verified":
                score *= 1.2 # 20% boost for verified functions

            results.append(
                {
                    "name": name,
                    "score": score,
                    "status": status,
                    "description": p.get("description", ""),
                }
            )
        
        # Re-sort based on boosted score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    finally:
        conn.close()


def _resolve_bundle(name: str, visited: Set[str], codes: List[str]):
    """Local bottom-up dependency resolution."""
    if name in visited:
        return
    visited.add(name)
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT code, metadata FROM functions WHERE name = ?", (name,)
        ).fetchone()
        if row:
            code, meta_json = row
            meta = json.loads(meta_json)
            for dep in meta.get("internal_dependencies", []):
                _resolve_bundle(dep, visited, codes)
            codes.append(f"# --- {name} ---\n{code}")
    finally:
        conn.close()


def do_get_impl(asset_name: str, integrate_dependencies: bool = False) -> str:
    """Local retrieval."""
    if integrate_dependencies:
        visited = set()
        codes = []
        _resolve_bundle(asset_name, visited, codes)
        return "\n\n".join(codes) if codes else "Not found."

    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT code FROM functions WHERE name = ?", (asset_name,)
        ).fetchone()
        return row[0] if row else f"Function '{asset_name}' not found."
    finally:
        conn.close()


def do_get_details_impl(name: str) -> Dict:
    """Gets full metadata for a local function."""
    conn = get_db_connection()
    try:
        sql = "SELECT name, status, description, tags, call_count, last_called_at, code, metadata FROM functions WHERE name = ?"
        row = conn.execute(sql, [name]).fetchone()
        if not row:
            return {"error": f"Function '{name}' not found"}
        return {
            "name": row[0],
            "status": row[1],
            "description": row[2],
            "tags": json.loads(row[3]) if row[3] else [],
            "call_count": row[4],
            "last_called_at": row[5],
            "code": row[6],
            "metadata": json.loads(row[7]) if row[7] else {},
        }
    finally:
        conn.close()


def do_delete_impl(asset_name: str) -> str:
    """Local deletion."""
    with DBWriteLock():
        conn = get_db_connection()
        try:
            conn.execute(
                "DELETE FROM embeddings WHERE function_name = ?", (asset_name,)
            )
            conn.execute("DELETE FROM functions WHERE name = ?", (asset_name,))
            get_vector_db().delete(asset_name)
            conn.commit()
            return f"SUCCESS: Function '{asset_name}' deleted locally."
        finally:
            conn.close()


def do_list_impl(limit: int = 100) -> List[Dict]:
    """Local listing."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT name, status, description FROM functions LIMIT ?", (limit,)
        ).fetchall()
        return [{"name": r[0], "status": r[1], "description": r[2]} for r in rows]
    finally:
        conn.close()


def do_smart_get_impl(query: str, target_dir: str = "./") -> Dict:
    """Hybrid: Local Search -> Hub Rerank -> Local Injection."""
    candidates = do_search_impl(query, limit=5)
    if not candidates:
        return {"status": "error", "message": "No local candidates found."}

    selected_name = candidates[0]["name"]
    try:
        hub_rerank_url = f"{HUB_URL.rstrip('/')}/api/v1/intelligence/rerank/direct"
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                hub_rerank_url,
                json={
                    "query": query,
                    "candidates": [
                        {"name": c["name"], "description": c.get("description", ""), "tags": c.get("tags", [])}
                        for c in candidates
                    ]
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("selected_name"):
                    selected_name = data["selected_name"]
                    logger.info(f"Edge: Hub selected '{selected_name}' as best match.")
            elif resp.status_code == 429:
                logger.warning("Edge: Hub is rate limited. Falling back to local top match.")
            else:
                logger.error(f"Edge: Hub rerank failed ({resp.status_code}): {resp.text}")
    except Exception as e:
        logger.warning(f"Edge: Hub Rerank failed (network/other): {e}. Falling back to local top match.")

    from edge.generator import PackageGenerator

    code = do_get_impl(selected_name)
    inject_res = PackageGenerator.inject_package(
        target_dir, [{"name": selected_name, "code": code}]
    )

    return {
        "status": "success",
        "selected_function": selected_name,
        "injection_summary": inject_res,
    }
