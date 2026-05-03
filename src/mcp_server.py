import logging
import os
from contextlib import asynccontextmanager

from fastmcp import FastMCP

import orchestrator
from core.exceptions import LogicHiveError, SyntaxValidationError, ValidationError
from orchestrator import (
    do_delete_async,
    do_get_verification_status,
    do_save_async,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Initializes and cleans up the background worker for environment pooling."""
    from core.execution.pool import PoolManager

    manager = PoolManager.get_instance()
    await manager.initialize()
    try:
        yield
    finally:
        await manager.shutdown()


# Initialize FastMCP server with lifespan management
mcp = FastMCP(
    "LogicHive",
    description="Quality-Gated Code Asset Vault for Agentic Workflows",
    lifespan=lifespan,
)


@mcp.tool()
async def save_function(
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
    wait_for_previous: bool = False,
) -> str:
    """
    Saves a verified, high-quality code asset to the LogicHive vault for future reuse.
    The asset undergoes an automated Quality Gate check (AI grading & Static analysis).

    BEST PRACTICES FOR AI AGENTS:
    1. Strategy Priority (Purity > Utility):
       - PRIMARY: Extract pure logic from I/O code. Save only the "Logic Atom" (data processing, validation).
       - SECONDARY: If you must save I/O-heavy code (e.g. retry patterns), use 'mock_imports' to bypass network/file calls.
    2. Project Context: Always specify a 'project' name to avoid cluttering the global vault.
    3. Metadata is Critical: Provide a detailed 'description' (min 10 chars).
    4. Self-Test: Always include 'test_code'. Use mocks for I/O functions to ensure deterministic verification.
    5. Smart Mocking: Add heavy libraries (torch) or I/O libraries (aiohttp, httpx) to 'mock_imports'.
    REJECTION CRITERIA:
    - Syntax errors (instant Score 0 / Critical failure).
    - Vague descriptions or missing tags.
    - Poor AI-graded quality (logic flaws, security risks).
    - **Quality Theater**: Literal assertions (e.g., `assert True`) or tests that don't call the code.

    SUPPORTED LANGUAGES:
    - **Python** (High Fidelity): Full AST-based verification, assertion analysis, and runtime pool execution.
    - **JavaScript / TypeScript** (Standard): Structural assertion detection and pattern matching.
    - **C++ / Java** (Foundational): Keyword-based asset integrity checks.
    """
    logger.info(f"[TRACE] MCP: Tool 'save_function' called for '{name}' [project={project}]")

    try:
        # 1. Trigger Async Save
        success = await do_save_async(
            name=name,
            code=code,
            description=description,
            language=language,
            tags=tags,
            test_code=test_code,
            dependencies=dependencies,
            project=project,
            mock_imports=mock_imports,
            timeout=timeout,
        )

        return (
            f"Asset '{name}' has been successfully submitted to the project '{project}'.\n"
            "Status: PENDING (Verification in progress). Use 'get_verification_status' to check results."
            if success
            else "Failed to initiate save (Unknown Error)"
        )
    except SyntaxValidationError as e:
        # User feedback Tip #3: Prominent Syntax Error Reporting
        details = e.details or {}
        eval_details = details.get("eval_details", {}).get("static_analysis", {})
        inner_details = eval_details.get("details", {})

        line = inner_details.get("line", "?")
        offset = inner_details.get("offset", "?")
        text = inner_details.get("text", "N/A")

        md = [
            f"### ❌ IMMEDIATE REJECTION: Syntax Error",
            f"**Message**: {str(e)}",
            f"- **Line**: {line}",
            f"- **Offset**: {offset}",
            f"\n**Context**:\n```python\n{text.strip()}\n```",
            "\nPlease correct the syntax before attempting to save again.",
        ]
        return "\n".join(md)
    except ValidationError as e:
        # Extract rich details for better transparency (User feedback Tip #1)
        details = e.details or {}
        reason = details.get("reason", str(e))
        eval_details = details.get("eval_details", {})

        md = [
            f"### ⚠️ Save Rejected: Validation Error",
            f"**Reason**: {reason}",
        ]

        if eval_details:
            md.append("\n#### Validation Details:")
            for tool, res in eval_details.items():
                md.append(f"- **{tool.title()}**: {res.get('reason', 'N/A')}")

        return "\n".join(md)
    except LogicHiveError as e:
        logger.error(f"MCP Server: LogicHiveError in save_function: {e}")
        return f"LogicHive Error: {str(e)}"
    except Exception as e:
        logger.exception(f"MCP Server: Unexpected error in save_function: {e}")
        return f"System Error: An unexpected infrastructure error occurred. {str(e)}"


@mcp.tool()
async def search_functions(
    query: str,
    limit: int = 5,
    language: str | None = None,
    project: str = "default",
    wait_for_previous: bool = False,
) -> str:
    """
    Search for high-quality, reusable code functions within the LogicHive vault using Hybrid Search.
    This is the primary tool for knowledge retrieval. Use it when you need to find existing
    implementations or avoid reinventing code.

    NOTE: This tool returns technical SUMMARIES (metadata) only. To see the full source code
    of a function, use the 'get_function' tool with the name and project found in these results.

    SEARCH MODES:
    1. Semantic Search: Natural language queries (e.g., "authentication helper").
    2. Exact Match: Function names (e.g., "normalize_llm_args").
    3. Tag Filter: Use "#tagname" (e.g., "#security").
    4. Language Filter: Specify the language (e.g., "python", "javascript") to restrict results.
    5. Project Filter: Restrict search to a specific project (e.g., "ayato-studio").
    """
    from orchestrator import do_search_async

    logger.info(f"[TRACE] MCP: Tool 'search_functions' called with query: '{query}'")

    try:
        results = await do_search_async(
            query=query, limit=limit, language=language, project=project
        )

        if not results:
            return f"No functions found matching query '{query}' in project '{project}'."

        md = f"## Search Results for: {query}\n\n"
        for i, res in enumerate(results, 1):
            name = res.get("name")
            proj = res.get("project", project)
            desc = res.get("description", "No description")
            score = res.get("score", 0)
            summary = res.get("technical_summary", "N/A")
            tags = ", ".join([f"`{t}`" for t in res.get("tags", [])])

            md += f"### {i}. {name} (Project: {proj})\n"
            md += f"- **Match Score**: {score:.2f}\n"
            md += f"- **Description**: {desc}\n"
            md += f"- **Technical Summary**: {summary}\n"
            md += f"- **Tags**: {tags}\n\n"

        return md
    except Exception as e:
        logger.exception(f"MCP Server: Error in search_functions: {e}")
        return f"Search Error: {str(e)}"


@mcp.tool()
async def list_functions(
    project: str | None = None,
    tags: list[str] | None = None,
    limit: int = 50,
    wait_for_previous: bool = False,
) -> str:
    """
    List high-quality code functions with optional filtering by project and tags.
    Use this to browse available assets when search_functions is too specific.
    """
    from storage.sqlite_api import sqlite_storage

    logger.info(f"[TRACE] MCP: Tool 'list_functions' called.")

    try:
        results = await sqlite_storage.list_functions(project=project, tags=tags, limit=limit)

        if not results:
            return "No functions found in the vault."

        md = "## Available Functions\n\n"
        md += "| Name | Project | Language | Score | Tags |\n"
        md += "| :--- | :--- | :--- | :--- | :--- |\n"
        for res in results:
            tags_str = ", ".join(res.get("tags", []))
            md += f"| {res['name']} | {res['project']} | {res['language']} | {res['score']:.1f} | {tags_str} |\n"

        return md
    except Exception as e:
        return f"Error listing functions: {str(e)}"


@mcp.tool()
async def get_function(
    name: str, project: str = "default", wait_for_previous: bool = False
) -> str:
    """
    Fetch the full source code and metadata of a specific function by its exact name and project.
    Use this AFTER search_functions if you've identified a promising candidate name.
    """
    from storage.sqlite_api import sqlite_storage

    logger.info(f"[TRACE] MCP: Tool 'get_function' called for '{name}' [project={project}]")

    try:
        func = await sqlite_storage.get_function(name, project)

        if not func:
            return f"Asset '{name}' not found in project '{project}'."

        md = f"## Function: {name}\n"
        md += f"- **Project**: {func['project']}\n"
        md += f"- **Language**: {func['language']}\n"
        md += f"- **Score**: {func['score']:.1f}\n"
        md += f"- **Status**: {func['status'].upper()}\n"
        md += f"- **Description**: {func['description']}\n"

        if func.get("technical_summary"):
            md += f"- **Technical Summary**: {func['technical_summary']}\n"

        md += f"\n### Source Code\n```python\n{func['code']}\n```\n"

        if func.get("dependencies"):
            md += f"\n### Dependencies\n`{', '.join(func['dependencies'])}`"

        return md
    except Exception as e:
        return f"Error retrieving function: {str(e)}"


@mcp.tool()
async def delete_function(
    name: str, project: str = "default", wait_for_previous: bool = False
) -> str:
    """
    Deletes a function from the LogicHive vault for a specific project.
    The function is archived in the backup repository for safety.
    """
    logger.info(f"[TRACE] MCP: Tool 'delete_function' called for '{name}' [project={project}]")

    try:
        success = await do_delete_async(name, project)
        if success:
            return f"Asset '{name}' has been successfully deleted from project '{project}'."
        else:
            return f"Asset '{name}' not found or could not be deleted."
    except Exception as e:
        return f"Error deleting function: {str(e)}"


@mcp.tool()
async def check_integrity(wait_for_previous: bool = False) -> str:
    """
    Performs a comprehensive integrity check of the LogicHive system,
    including DB status, Vector store synchronization, and Environment pools.
    """
    from core.config import FAISS_INDEX_PATH, SQLITE_DB_PATH
    from storage.sqlite_api import sqlite_storage
    from storage.vector_store import vector_manager

    logger.info("[TRACE] MCP: Tool 'check_integrity' called.")

    status = ["## LogicHive System Integrity Report\n"]

    try:
        # 1. Database Check
        db_exists = os.path.exists(SQLITE_DB_PATH)
        status.append(
            f"### 1. Database (SQLite)\n- Path: `{SQLITE_DB_PATH}`\n- Status: {'✅ Online' if db_exists else '❌ Offline'}"
        )
        count = 0
        if db_exists:
            count = await sqlite_storage.get_function_count()
            status.append(f"- Total Assets: {count}")

        # 2. Vector Store Check
        faiss_exists = os.path.exists(FAISS_INDEX_PATH)
        status.append(
            f"### 2. Vector Store (FAISS)\n- Path: `{FAISS_INDEX_PATH}`\n- Status: {'✅ Found on disk' if faiss_exists else '⚠️ Missing'}"
        )

        if faiss_exists and db_exists:
            # Check for memory sync (Silent check for initialization)
            if not vector_manager._initialized:
                status.append("- **Memory State**: 💤 Uninitialized (Will load on first search)")
            else:
                idx_size = vector_manager.index.ntotal if vector_manager.index else 0
                if idx_size != count:
                    status.append(
                        f"- **Desync Detected**: DB({count}) vs FAISS-Memory({idx_size}). Rebuild recommended."
                    )
                else:
                    status.append(f"- Sync Status: ✅ Optimal ({idx_size} vectors in memory)")

        # 3. Environment Pool Check
        from core.execution.pool import PoolManager

        pool = PoolManager.get_instance()
        status.append(
            f"### 3. Execution Pool\n- Initialized: {'✅ Yes' if pool._initialized else '❌ No'}"
        )
        if pool._initialized:
            active_envs = len(pool._pool)
            status.append(f"- Warm Environments: {active_envs}")

        return "\n".join(status)
    except Exception as e:
        return f"Error during integrity check: {str(e)}"


@mcp.tool()
async def get_verification_status(
    name: str, project: str = "default", wait_for_previous: bool = False
) -> str:
    """
    Checks the progress and detailed report of a background verification task.
    Use this to see if a recently saved function passed the Quality Gate.
    """
    logger.info(f"[TRACE] MCP: Tool 'get_verification_status' called for '{name}' [project={project}]")

    try:
        # Re-align with orchestrator's function name
        f_data = await do_get_verification_status(name, project=project)

        if f_data.get("status") == "not_found":
            logger.warning(f"[TRACE] MCP: Asset '{name}' not found.")
            return f_data["message"]

        status = f_data.get("status", "unknown")
        report = f_data.get("report")

        md = f"### Verification Status: {name}\n"
        md += f"- **Current Status**: {status.upper()}\n"
        if status == "verified":
            md += "Quality Gate passed. Asset is active in the vault.\n"
        elif status == "pending":
            md += "Verification is still in progress. Please check back shortly.\n"
        elif status == "failed":
            md += "Quality Gate rejected the asset. Review the report below for details.\n"
        elif status == "error":
            md += "A system error occurred during verification. Infrastructure might be unstable.\n"

        if isinstance(report, dict):
            md += "\n\n#### Detailed Report:\n"
            if "error" in report:
                md += f"**Error Details**: {report['error']}\n"
            elif "reason" in report:
                md += f"- **Reason**: {report.get('reason', 'N/A')}\n"
                details = report.get("details", {})
                for tool, res in details.items():
                    md += (
                        f"- **{tool.title()}**: {res.get('score', 0):.1f} ({res.get('reason', 'N/A')})\n"
                    )
            else:
                import json

                md += f"```json\n{json.dumps(report, indent=2)}\n```"
        elif report:
            md += f"\n\n#### Raw Report:\n```json\n{report}\n```"

        return md
    except Exception as e:
        return f"Error retrieving status: {str(e)}"


@mcp.tool()
async def rebuild_index(wait_for_previous: bool = False) -> str:
    """
    Forcefully rebuilds the FAISS vector index from all embeddings stored in the database.
    Use this if 'check_integrity' reports a desync between DB and Vector Store.
    """
    from storage.vector_store import vector_manager

    try:
        logger.info("[TRACE] MCP: Tool 'rebuild_index' called.")
        await vector_manager.rebuild_index()
        return "Vector index has been successfully rebuilt from database records."
    except Exception as e:
        logger.error(f"MCP Server: Error in rebuild_index: {e}")
        return f"LogicHive Error: Failed to rebuild index. Detail: {str(e)}"


if __name__ == "__main__":
    mcp.run()
