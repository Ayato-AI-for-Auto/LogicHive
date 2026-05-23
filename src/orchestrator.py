# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import ast
import asyncio
import re
import uuid
from typing import Any

from core.config import (
    DESCRIPTION_MIN_LENGTH,
    ENABLE_AUTO_BACKUP,
    GEMINI_API_KEY,
    GITHUB_TOKEN,
    QUALITY_GATE_THRESHOLD,
)
from core.consolidation import LogicIntelligence
from core.evaluation.manager import EvaluationManager
from core.exceptions import SyntaxValidationError, ValidationError
from core.hash_utils import calculate_code_hash
from core.logging_config import get_logger
from core.tracer import trace_execution
from storage.sqlite_api import sqlite_storage
from storage.vector_store import vector_manager

logger = get_logger(__name__)

# --- Resource Constraints ---
# Limit concurrent search requests to prevent LLM pipeline instability
search_semaphore = asyncio.Semaphore(3)

# --- Helpers ---


def extract_dependencies(code: str, language: str = "python") -> list[str]:
    """
    Extracts dependencies based on language.
    Python uses AST, while others use optimized regex.
    """
    dependencies = set()
    lang = language.lower()

    if lang == "python":
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        base = alias.name.split(".")[0]
                        dependencies.add(base)
                elif isinstance(node, ast.ImportFrom):
                    if node.level == 0 and node.module:
                        base = node.module.split(".")[0]
                        dependencies.add(base)
        except Exception as e:
            logger.warning(f"Orchestrator: AST extraction failed, falling back to regex: {e}")
            # Fallback to regex for Python if AST fails
            matches = re.findall(r"^(?:import|from)\s+([a-zA-Z0-9_]+)", code, re.MULTILINE)
            dependencies.update(matches)

    elif lang in ["typescript", "javascript", "tsx", "jsx"]:
        # Regex for ES6 imports: from 'pkg' or from "pkg" (robust whitespace)
        es6_matches = re.findall(r"from\s+['\"]([^'\"./][^'\"]*)['\"]", code)
        # Regex for CommonJS: require('pkg')
        cjs_matches = re.findall(r"require\s*\(\s*['\"]([^'\"./][^'\"]*)['\"]\s*\)", code)
        # Simple import 'pkg'
        simple_matches = re.findall(r"import\s+['\"]([^'\"./][^'\"]*)['\"]", code)

        all_matches = es6_matches + cjs_matches + simple_matches
        for pkg in all_matches:
            # Extract scope if present (e.g. @types/node -> @types/node, but lodash/fp -> lodash)
            if pkg.startswith("@"):
                parts = pkg.split("/")
                if len(parts) >= 2:
                    dependencies.add(f"{parts[0]}/{parts[1]}")
                else:
                    dependencies.add(pkg)
            else:
                dependencies.add(pkg.split("/")[0])

    # Clean up standard libs/internal refs
    std_lib = {
        "os",
        "sys",
        "json",
        "math",
        "datetime",
        "typing",
        "asyncio",
        "logging",
        "ast",
        "pathlib",
        "abc",
        "fs",
        "path",
        "http",
        "https",
        "crypto",
    }
    return sorted(dependencies - std_lib)


@trace_execution
async def do_delete_async(name: str, project: str = "default") -> bool:
    """
    Orchestrates deletion from DB, Vector index, and archiving in Backup.
    """
    logger.info(f"[TRACE] Orchestrator: Initiating deletion of '{name}' [project={project}]")
    try:
        # 1. Local DB deletion
        db_success = await sqlite_storage.delete_function(name, project=project)
        if not db_success:
            logger.warning(f"[TRACE] Orchestrator: Failed to find/delete '{name}' in DB.")
            return False

        # 2. Vector index deletion (background)
        asyncio.create_task(vector_manager.remove_vector(name, project=project))

        # 3. Backup Archiving (background)
        if ENABLE_AUTO_BACKUP and GITHUB_TOKEN:
            from storage.auto_backup import backup_manager

            asyncio.create_task(backup_manager.archive_asset(name, project=project))

        logger.info(f"[TRACE] Orchestrator: Deletion of '{name}' successful.")
        return True
    except Exception as e:
        logger.error(f"[TRACE] Orchestrator: Deletion failed for '{name}': {e}", exc_info=True)
        raise


# --- MCP / REST API Implementation Wrappers ---


@trace_execution
async def _run_async_verification_pipeline(
    name: str,
    project: str,
    code: str,
    description: str,
    tags: list[str],
    language: str,
    dependencies: list[str],
    test_code: str,
    mock_imports: list[str],
    timeout: int | None,
):
    """Background task to run Quality Gate, metadata enrichment and embedding generation."""
    try:
        logger.info(
            f"[TRACE] Orchestrator: Starting background verification for {name} [{project}]"
        )

        # 1. Quality Gate
        eval_manager = EvaluationManager()
        eval_res = await eval_manager.evaluate_all(
            code,
            language,
            description=description,
            tags=tags,
            test_code=test_code,
            dependencies=dependencies,
            mock_imports=mock_imports,
            timeout=timeout,
        )

        final_score = float(eval_res["score"])
        is_system_error = eval_res.get("is_system_error", False)
        logger.info(
            f"[DEBUG] Orchestrator Verification: score={final_score}, is_system_error={is_system_error}"
        )
        status = "verified" if final_score >= QUALITY_GATE_THRESHOLD else "failed"
        if is_system_error:
            status = "error"

        # 2. Metadata Enrichment (if needed)
        intel = LogicIntelligence(GEMINI_API_KEY)
        if not description or len(description) < DESCRIPTION_MIN_LENGTH or not tags:
            enriched = await intel.optimize_metadata(code)
            description = enriched.get("description", description)
            tags = list(set(tags + enriched.get("tags", [])))

        # 3. Embedding
        search_doc = intel.construct_search_document(name, description, tags, code)
        embedding = await intel.generate_embedding(search_doc)

        # 4. Update DB with final results
        await sqlite_storage.update_verification_status(
            name,
            project,
            status=status,
            report=eval_res,
            reliability_score=final_score,
        )

        # 5. Sync to Vector Store (if verified)
        if status == "verified":
            await vector_manager.upsert_vector(
                name,
                embedding,
                metadata={"project": project, "language": language},
                project=project,
            )

        logger.info(
            f"[TRACE] Orchestrator: Async verification FINISHED for '{name}' with status: {status}"
        )

    except Exception as e:
        logger.error(
            f"[TRACE] Orchestrator: Async verification FAILED for '{name}': {e}", exc_info=True
        )
        await sqlite_storage.update_verification_status(
            name, project, status="error", report={"error": str(e)}
        )


@trace_execution
async def do_save_async(
    name: str,
    code: str,
    description: str = "",
    tags: list[str] | None = None,
    language: str = "python",
    dependencies: list[str] | None = None,
    test_code: str = "",
    project: str = "default",
    mock_imports: list[str] | None = None,
    timeout: int | None = None,
):
    """
    Asynchronously saves a function.
    1. Checks for hash-based deduplication.
    2. Saves with 'pending' status.
    3. Kicks off background verification and returns immediately.
    """
    if tags is None:
        tags = []
    if dependencies is None:
        dependencies = []
    if mock_imports is None:
        mock_imports = []
    # 1. Deduplication Check
    code_hash = calculate_code_hash(code)
    existing = await sqlite_storage.get_function_by_hash(code_hash, project)
    if existing:
        logger.info(
            f"Orchestrator: Deduplication hit for '{name}' (Existing: '{existing['name']}')"
        )
        raise ValidationError(
            f"Asset with identical logic is already registered as '{existing['name']}' in project '{project}'."
        )

    # 2. Synchronous Critical Checks (Quality Gate Tip #1: Early Rejection)
    eval_manager = EvaluationManager()

    # Structural Check (Language-Agnostic)
    structural = eval_manager.get_evaluator("structural")
    if structural:
        struct_res = await structural.evaluate(code, language)
        if struct_res.score == 0:
            raise SyntaxValidationError(
                f"Structural Error: {struct_res.reason}",
                details={
                    "score": 0.0,
                    "reason": "Immediate Rejection: Structural integrity failed.",
                    "eval_details": {"structural": struct_res},
                },
            )

    # Python-Specific Static Check
    if language.lower() == "python":
        python_static = eval_manager.get_evaluator("python_static")
        if python_static:
            static_res = await python_static.evaluate(code, language)
            if static_res.score == 0:
                raise SyntaxValidationError(
                    f"Python Static Error: {static_res.reason}",
                    details={
                        "score": 0.0,
                        "reason": "Immediate Rejection: Critical static check failed.",
                        "eval_details": {"python_static": static_res},
                    },
                )

    # 3. Immediate Save (Pending)
    from core.system_info import SystemFingerprint

    # Automatic Dependency Extraction (Immediate)
    if not dependencies:
        extracted = extract_dependencies(code, language=language)
        dependencies = extracted if extracted else []

    data = {
        "id": str(uuid.uuid4()),
        "name": str(name),
        "code": str(code),
        "description": str(description),
        "language": str(language),
        "tags": tags,
        "reliability_score": 0.0,
        "embedding": None,  # Will be updated by bg task
        "code_hash": str(code_hash),
        "dependencies": dependencies,
        "test_code": test_code,
        "project": project,
        "env_fingerprint": SystemFingerprint.get_current(),
        "verification_status": "pending",
        "verification_report": None,
    }

    # Initial save to DB
    logger.info(
        f"[TRACE] Orchestrator: Saving initial 'pending' record for '{name}' [project={project}]"
    )
    save_result = await sqlite_storage.upsert_function(data)
    if not save_result:
        raise Exception("Failed to perform initial save to LogicHive vault.")

    # 4. Kick off Background Verification
    asyncio.create_task(
        _run_async_verification_pipeline(
            name,
            project,
            code,
            description,
            tags,
            language,
            dependencies,
            test_code,
            mock_imports,
            timeout,
        )
    )

    logger.info(f"Orchestrator: Save accepted for '{name}'. Verification is running in background.")
    return True


@trace_execution
async def do_get_async(name: str, project: str = "default") -> dict[str, Any] | None:
    """Asynchronous implementation for getting a function."""
    return await sqlite_storage.get_function_by_name(name, project=project)


@trace_execution
async def do_search_async(
    query: str, limit: int = 5, language: str | None = None, project: str = "default"
):
    """Asynchronous implementation for searching functions with Query Expansion and Re-ranking."""
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            async with search_semaphore:
                intel = LogicIntelligence(GEMINI_API_KEY)

                expanded_query = await intel.expand_query(query)
                query_emb = await intel.generate_embedding(expanded_query)

                logger.info(
                    f"Orchestrator: Performing hybrid search for '{query}' (Lang: {language}, Project: {project}, Attempt: {attempt + 1})"
                )

                # 1. Fetch more candidates than requested for re-ranking (limit * 3)
                initial_results = await sqlite_storage.find_similar_functions(
                    query_emb,
                    query_text=query,
                    limit=limit * 3,
                    language=language,
                    project=project,
                    include_code=False,
                )

                if not initial_results:
                    return []

                # 2. Re-rank using LLM
                logger.info(f"Orchestrator: Re-ranking {len(initial_results)} candidates...")
                reranked_results = await intel.rerank_results(query, initial_results, limit=limit)

                # 3. Fallback: Auto-Draft Generation (Experimental)
                top_score = reranked_results[0].get("similarity", 0) if reranked_results else 0
                generation_keywords = ["create", "generate", "make", "implement", "write", "how to"]
                is_generation_request = any(k in query.lower() for k in generation_keywords)

                if top_score < 0.45 and is_generation_request:
                    logger.info(
                        f"Orchestrator: Weak results (Score: {top_score:.2f}) and Generation intent detected. Triggering..."
                    )
                    from core.plugins.draft_generator import DraftGenerator

                    generator = DraftGenerator(intel)
                    draft = await generator.generate_draft(
                        query, initial_results, language=language or "python"
                    )
                    if draft:
                        draft["similarity"] = 0.4
                        draft["project"] = project or "default"
                        return [draft] + reranked_results

                return reranked_results
        except Exception as e:
            last_error = e
            logger.warning(f"Orchestrator: Search attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0 * (attempt + 1))  # Exponential-ish backoff
            else:
                logger.error(f"Orchestrator: All search retries exhausted for '{query}'")
                raise last_error from e


@trace_execution
async def do_list_async(
    project: str | None = None, tags: list[str] | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    """Lists functions with optional filtering."""
    return await sqlite_storage.get_functions(project=project, tags=tags, limit=limit)


@trace_execution
async def check_integrity() -> dict[str, Any]:
    """
    Checks the health of various components (Database, Vector Index, Pool).
    """
    from core.execution.pool import PoolManager
    from storage.sqlite_api import sqlite_storage
    from storage.vector_store import vector_manager

    details = {}

    # 1. DB Check
    db_health = await sqlite_storage.check_health()
    details["database"] = db_health

    # 2. Vector Store Check
    vector_health = await vector_manager.check_health()
    details["vector_store"] = vector_health

    # 3. Pool Check
    pool_manager = PoolManager.get_instance()
    pool_health = await pool_manager.check_health()
    details["pool_manager"] = pool_health

    status = "Healthy"
    if any(h.get("status") == "Error" for h in details.values()):
        status = "Error"
    elif any(h.get("status") == "Warning" for h in details.values()):
        status = "Warning"

    return {"status": status, "details": details}


@trace_execution
async def do_get_verification_status(name: str, project: str = "default") -> dict[str, Any]:
    """Retrieves the verification status and report for a function."""
    logger.info(
        f"[TRACE] Orchestrator: Fetching verification status for '{name}' [project={project}]"
    )
    func = await sqlite_storage.get_function_by_name(name, project)
    if not func:
        logger.warning(f"[TRACE] Orchestrator: Asset '{name}' not found during status check.")
        return {
            "status": "not_found",
            "message": f"Asset '{name}' not found in project '{project}'.",
        }

    return {
        "name": name,
        "project": project,
        "status": func.get("verification_status", "unknown"),
        "score": func.get("reliability_score", 0),
        "report": func.get("verification_report"),
    }
