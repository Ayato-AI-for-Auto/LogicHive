import ast
import asyncio
import logging
from typing import Any

from core.config import GEMINI_API_KEY
from core.consolidation import LogicIntelligence
from core.evaluation.manager import EvaluationManager
from core.exceptions import SyntaxValidationError, ValidationError
from core.hash_utils import calculate_code_hash
from storage.sqlite_api import sqlite_storage
from storage.vector_store import vector_manager

logger = logging.getLogger(__name__)

# --- Resource Constraints ---
# Limit concurrent search requests to prevent LLM pipeline instability
search_semaphore = asyncio.Semaphore(3)

# --- Helpers ---


def extract_dependencies(code: str) -> list[str]:
    """Extracts top-level imports from Python code."""
    try:
        tree = ast.parse(code)
        deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    deps.append(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    deps.append(node.module.split(".")[0])
        return list(set(deps))
    except Exception as e:
        logger.warning(f"Orchestrator: Could not parse code for dependencies: {e}")
        # Fallback to regex or return empty
        return []


# --- Core Logic Implementation ---


async def _run_async_verification_pipeline(
    name: str,
    code: str,
    description: str,
    tags: list[str],
    project: str,
    language: str,
    test_code: str | None = None,
    dependencies: list[str] | None = None,
    mock_imports: list[str] | None = None,
    timeout: int = 60,
):
    """
    Internal pipeline that runs evaluation and updates status in the background.
    """
    intel = LogicIntelligence(GEMINI_API_KEY)

    try:
        # 1. Quality Gate
        eval_manager = EvaluationManager()
        eval_res = await eval_manager.evaluate_all(
            code=code,
            language=language,
            test_code=test_code,
            dependencies=dependencies,
            mock_imports=mock_imports,
            timeout=timeout,
        )

        final_score = eval_res.get("score", 0.0)
        status = "verified" if final_score >= 70 else "failed"

        # 2. Consolidation (AI Grading)
        # If passed quality gate, generate technical summary and optimize tags
        consolidated = {}
        if status == "verified":
            consolidated = await intel.consolidate_asset(name, code, description)

        # 3. Embedding
        search_doc = intel.construct_search_document(name, description, tags, code)
        embedding = await intel.generate_embedding(search_doc)

        # 4. Final Update
        await sqlite_storage.update_function_verification(
            name=name,
            project=project,
            status=status,
            score=final_score,
            report=eval_res,
            technical_summary=consolidated.get("summary"),
            optimized_tags=consolidated.get("tags"),
            embedding=embedding,
        )

        # 5. Index Update (Only if verified)
        if status == "verified":
            await vector_manager.upsert_vector(name, project, embedding)

        logger.info(f"[TRACE] Orchestrator: Async verification completed for '{name}': {status}")

    except Exception as e:
        logger.exception(f"[TRACE] Orchestrator: Async verification FAILED for '{name}': {e}")
        await sqlite_storage.update_function_verification(
            name=name, project=project, status="error", report={"error": str(e)}
        )


async def do_save_async(
    name: str,
    code: str,
    description: str,
    language: str = "python",
    tags: list[str] | None = None,
    test_code: str | None = None,
    dependencies: list[str] | None = None,
    project: str = "default",
    mock_imports: list[str] | None = None,
    timeout: int = 60,
) -> bool:
    """
    Entry point for saving a function.
    Performs immediate DB entry and kicks off background evaluation.
    """
    tags = tags or []
    dependencies = dependencies or []

    # 1. Logic Hash Check (Prevent Duplicates)
    logic_hash = calculate_code_hash(code)
    existing = await sqlite_storage.get_function_by_hash(logic_hash, project)
    if existing:
        logger.info(f"Orchestrator: Logic already exists as '{existing['name']}'")
        raise ValidationError(
            f"Asset with identical logic is already registered as '{existing['name']}' in project '{project}'."
        )

    # 2. Synchronous Syntax Check (Quality Gate Tip #1: Early Rejection)
    if language.lower() == "python":
        try:
            ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Orchestrator: Synchronous syntax check failed for '{name}': {e}")
            raise SyntaxValidationError(
                f"Python Syntax Error: {e.msg} (Line {e.lineno})",
                details={
                    "score": 0.0,
                    "reason": "Immediate Rejection: Invalid Python syntax.",
                    "eval_details": {
                        "static_analysis": {
                            "score": 0.0,
                            "reason": f"Syntax Error: {str(e)}",
                            "details": {"line": e.lineno, "offset": e.offset, "text": e.text},
                        }
                    },
                },
            )

    # 3. Immediate Save (Pending)
    from core.system_info import SystemFingerprint

    # Automatic Dependency Extraction (Immediate)
    auto_deps = extract_dependencies(code)
    all_deps = list(set(dependencies + auto_deps))

    await sqlite_storage.save_function_pending(
        name=name,
        code=code,
        description=description,
        language=language,
        tags=tags,
        dependencies=all_deps,
        project=project,
        logic_hash=logic_hash,
        metadata={
            "fingerprint": SystemFingerprint.generate(),
            "has_tests": bool(test_code),
        },
    )

    # 4. Kickoff Async Pipeline
    asyncio.create_task(
        _run_async_verification_pipeline(
            name=name,
            code=code,
            description=description,
            tags=tags,
            project=project,
            language=language,
            test_code=test_code,
            dependencies=all_deps,
            mock_imports=mock_imports,
            timeout=timeout,
        )
    )

    return True


async def do_get_verification_status(name: str, project: str = "default") -> dict[str, Any]:
    """Retrieves the status and report for a specific function."""
    func = await sqlite_storage.get_function(name, project)
    if not func:
        return {"status": "not_found", "message": f"Asset '{name}' not found in vault."}

    return {
        "name": func["name"],
        "status": func["status"],
        "score": func["score"],
        "report": func["report"],
        "updated_at": func["updated_at"],
    }


async def do_search_async(
    query: str, limit: int = 5, language: str | None = None, project: str = "default"
):
    """Asynchronous implementation for searching functions with Query Expansion and Re-ranking."""
    async with search_semaphore:
        intel = LogicIntelligence(GEMINI_API_KEY)

        expanded_query = await intel.expand_query(query)
        query_emb = await intel.generate_embedding(expanded_query)

        logger.info(
            f"Orchestrator: Performing hybrid search for '{query}' (Lang: {language}, Project: {project})"
        )

    # 1. Fetch more candidates than requested for re-ranking (limit * 3)
    # Note: passing project to vector_manager for future-proofing internal filtering
    candidate_names = await vector_manager.search(query_emb, limit=limit * 3)

    if not candidate_names:
        # Fallback to simple keyword search if vector store is empty/fails
        return await sqlite_storage.search_functions(
            query, limit=limit, language=language, project=project
        )

    # 2. Get full records for candidates
    candidates = await sqlite_storage.get_functions_by_names(candidate_names, project)

    # 3. Filter by language if specified
    if language:
        candidates = [c for c in candidates if c["language"] == language]

    # 4. Re-ranking (LLM)
    # Re-ranking ensures that the semantic matches are truly relevant to the logic requested
    ranked_candidates = await intel.rank_candidates(query, candidates)

    return ranked_candidates[:limit]


async def do_delete_async(name: str, project: str = "default") -> bool:
    """Deletes a function from the vault and the vector index."""
    # 1. Delete from SQLite (and get the record first for confirmation)
    func = await sqlite_storage.get_function(name, project)
    if not func:
        return False

    success = await sqlite_storage.delete_function(name, project)

    # 2. Delete from FAISS index
    if success:
        # Note: VectorStore delete is often a no-op or handled by periodic rebuild
        # but we call it for completeness if implemented
        await vector_manager.delete_vector(name, project)

    return success
