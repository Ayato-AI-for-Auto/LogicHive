# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
import os
import sqlite3
import sys
from contextlib import asynccontextmanager

import fastmcp
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

import core.config
import core.network
import orchestrator
from core.config import CHROMA_DB_DIR, get_sqlite_db_path
from core.db import get_db_connection
from core.exceptions import LogicHiveError, SyntaxValidationError, ValidationError
from core.formatters import (
    format_report as _format_report,
    format_syntax_error as _format_syntax_error,
    format_validation_error as _format_validation_error,
    get_status_description as _get_status_description,
)
from core.logging_config import get_logger
from core.network import wait_on_error
from core.tracer import trace_execution
from core.vulnerability import (
    get_vulnerability_warning_msg as _get_vulnerability_warning_msg,
    periodic_vulnerability_scan_loop as _periodic_vulnerability_scan_loop,
)
from orchestrator import (
    do_delete_async,
    do_get_verification_status,
    do_save_async,
)
from storage.sqlite_api import sqlite_storage
from storage.vector_store import vector_manager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Initializes and cleans up background workers for environment pooling and vulnerability scanning."""
    from core.execution.pool import PoolManager

    manager = PoolManager.get_instance()
    await manager.initialize()

    scan_task = asyncio.create_task(_periodic_vulnerability_scan_loop())
    try:
        yield
    finally:
        scan_task.cancel()
        await manager.shutdown()


# Initialize FastMCP server with lifespan management
mcp = FastMCP("LogicHive", lifespan=lifespan)


@mcp.tool()
@trace_execution
async def search_functions(
    query: str,
    limit: int = 5,
    language: str = None,
    project: str = None,
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

    Args:
    query: Search term, exact name, or #tag.
    limit: Max results. Default 5.
    language: Optional language to filter by (e.g., 'python', 'javascript').
    project: Optional project name to narrow the search.
    wait_for_previous: Set to true to wait for all previously requested tools in this turn
        to complete before starting. Set to false (or omit) to run in parallel.
        Use true when this tool depends on the output of previous tools.
    """

    try:
        results = await orchestrator.do_search_async(query, limit, language, project=project)
        if not results:
            return "No matching functions found."

        md = "### Search Results\n\n"
        for res in results:
            is_draft = res.get("is_draft", False)
            name = res["name"]
            if is_draft:
                name = f"[AI-DRAFT] {name}"
            sim = res.get("similarity", 0)
            rel = res.get("reliability_score", 0) * 100
            desc = res.get("description", "No description")
            tags = ", ".join(res.get("tags", []))

            # Check for Environment Drift & Vulnerabilities
            drift_warning = ""
            stored_env = res.get("env_fingerprint")
            if stored_env:
                from core.system_info import SystemFingerprint

                if SystemFingerprint.compare(stored_env, SystemFingerprint.get_current()):
                    drift_warning = " [DRIFT]"

            vuln_warn = _get_vulnerability_warning_msg(res)
            if vuln_warn:
                drift_warning += " [VULNERABLE]"

            md += f"- **{name}{drift_warning}** (Match: {sim:.2f}, Reliability: {rel:.1f}%)\n"
            if is_draft:
                md += "  - *NOTE: This is a generated draft. Refine and Save to verify.*\n"
            if vuln_warn:
                md += f"  - *⚠️ {vuln_warn}*\n"
            md += f"  - *{desc}*\n"
            md += f"  - Tags: {tags}\n"
        return md
    except Exception as e:
        logger.error(f"MCP Server: Error in search_functions: {e}")
        return f"LogicHive Error: Failed to perform search. Detail: {str(e)}"


@mcp.tool()
@trace_execution
async def get_function(name: str, project: str = "default", wait_for_previous: bool = False) -> str:
    """
    Fetch the full source code and metadata of a specific function by its exact name and project.
    Use this AFTER search_functions if you've identified a promising candidate name.

    Args:
        name: The precise, case-sensitive name of the function (e.g., "save_log").
        project: The project namespace (defaults to 'default').
        wait_for_previous: Set to true to wait for all previously requested tools in this turn
            to complete before starting. Set to false (or omit) to run in parallel.
            Use true when this tool depends on the output of previous tools.
    """
    try:
        f_data = await orchestrator.do_get_async(name, project=project)
        if not f_data:
            return f"Function '{name}' not found"

        lang = f_data.get("language", "python")
        code = f_data["code"]
        desc = f_data.get("description", "No description")
        tags = ", ".join(f_data.get("tags", []))
        deps = ", ".join(f_data.get("dependencies", []))

        # Environment Drift & Vulnerability Checks
        drift_header = ""
        warnings_list = []

        stored_env = f_data.get("env_fingerprint")
        if stored_env:
            from core.system_info import SystemFingerprint
            warning = SystemFingerprint.generate_warning_msg(stored_env)
            if warning:
                warnings_list.append(warning)

        vuln_warn = _get_vulnerability_warning_msg(f_data)
        if vuln_warn:
            warnings_list.append(vuln_warn)

        if warnings_list:
            warning_txt = "\n\n".join(warnings_list)
            drift_header = f"> [!WARNING]\n> {warning_txt.replace(chr(10), chr(10) + '> ')}\n\n"

        response = (
            f"**Function: {name}**\n\n{drift_header}{desc}\n\n"
            f"**Tags:** {tags}\n**Dependencies:** {deps}\n\n"
            f"```{lang}\n{code}\n```"
        )
        return response
    except Exception as e:
        logger.error(f"MCP Server: Error in get_function: {name} - {e}")
        return f"LogicHive Error: Failed to retrieve function. Detail: {str(e)}"


@mcp.tool()
@trace_execution
async def save_function(
    name: str,
    code: str,
    description: str = "",
    language: str = "python",
    tags: list | None = None,
    dependencies: list[str] | None = None,
    test_code: str = "",
    project: str = "default",
    mock_imports: list[str] | None = None,
    timeout: int = 60,
    wait_for_previous: bool = False,
) -> str:
    if mock_imports is None:
        mock_imports = []
    try:
        success = await do_save_async(
            name=name,
            code=code,
            description=description,
            tags=tags,
            language=language,
            dependencies=dependencies,
            test_code=test_code,
            project=project,
            mock_imports=mock_imports,
            timeout=timeout,
        )
        if success:
            return (
                f"Asset '{name}' (Project: {project}) has been accepted and saved.\n"
                "Verification is running in the background. Use 'get_verification_status'."
            )
        return "Failed to initiate save (Unknown Error)"
    except SyntaxValidationError as e:
        return _format_syntax_error(e)
    except ValidationError as e:
        return _format_validation_error(e)
    except LogicHiveError as e:
        return (
            f"LogicHive SYSTEM ERROR: {str(e)}\n\n(This is likely a transient infrastructure "
            "issue, not a problem with your code. Please try again in a few moments.)"
        )
    except Exception as e:
        return f"Unexpected Error: {str(e)}"


@mcp.tool()
@trace_execution
async def debug_db(wait_for_previous: bool = False) -> str:
    """
    Debug tool to inspect LogicHive database configuration and table structure.

    Args:
        wait_for_previous: Set to true to wait for all previously requested tools in this turn
            to complete before starting. Set to false (or omit) to run in parallel.
            Use true when this tool depends on the output of previous tools.
    """

    db_path = get_sqlite_db_path()
    status = [f"SQLITE_DB_PATH: {db_path}"]
    status.append(f"Exists: {os.path.exists(db_path)}")

    if os.path.exists(db_path):
        try:
            status.append(f"Size: {os.path.getsize(db_path)} bytes")
            conn = sqlite3.connect(db_path)

            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            status.append(f"Tables: {tables}")
            conn.close()
        except Exception as e:
            status.append(f"Error reading DB: {e}")

    return "\n".join(status)


@mcp.tool()
@trace_execution
async def delete_function(
    name: str, project: str = "default", wait_for_previous: bool = False
) -> str:
    """
    Deletes a function from the LogicHive vault for a specific project.

    Args:
        name: The case-sensitive name of the function to delete.
        project: The project namespace (defaults to 'default').
        wait_for_previous: Set to true to wait for all previously requested tools in this turn
            to complete before starting. Set to false (or omit) to run in parallel.
            Use true when this tool depends on the output of previous tools.
    """
    success = await do_delete_async(name, project=project)
    if success:
        return f"Successfully deleted function '{name}' in project '{project}'."
    else:
        return f"Failed to delete function '{name}' in project '{project}'."


@mcp.tool()
@trace_execution
async def list_functions(
    project: str = None, tags: list[str] = None, limit: int = 50, wait_for_previous: bool = False
) -> str:
    """
    List high-quality code functions with optional filtering by project and tags.
    Use this to browse available assets when search_functions is too specific.

    Args:
        project: Optional project name to filter by.
        tags: Optional list of tags to filter by.
        limit: Max results. Default 50.
        wait_for_previous: Set to true to wait for all previously requested tools in this turn
            to complete before starting. Set to false (or omit) to run in parallel.
            Use true when this tool depends on the output of previous tools.
    """
    try:
        results = await orchestrator.do_list_async(project=project, tags=tags, limit=limit)
        if not results:
            return "No functions found in the vault."

        md = "### Vault Assets\n\n"
        for res in results:
            name = res["name"]
            project_name = res.get("project", "default")
            desc = res.get("description", "No description")
            tags_str = ", ".join(res.get("tags", []))
            rel = res.get("reliability_score", 0) * 100

            md += f"- **{name}** (Project: {project_name}, Reliability: {rel:.1f}%)\n"
            md += f"  - *{desc}*\n"
            md += f"  - Tags: {tags_str}\n"

        return md
    except Exception as e:
        logger.error(f"MCP Server: Error in list_functions: {e}")
        return f"LogicHive Error: Failed to list functions. Detail: {str(e)}"


@mcp.tool()
@trace_execution
async def check_integrity(wait_for_previous: bool = False) -> str:
    """
    Performs a comprehensive integrity check of the LogicHive system,
    including DB status, Vector store synchronization, and Environment pools.

    Args:
        wait_for_previous: Set to true to wait for all previously requested tools in this turn
            to complete before starting. Set to false (or omit) to run in parallel.
            Use true when this tool depends on the output of previous tools.
    """

    from storage.vector_store import vector_manager

    status = ["## LogicHive Integrity Report\n"]
    db_path = get_sqlite_db_path()

    try:
        # 1. DB Check
        db_exists = os.path.exists(db_path)
        status.append(
            f"### 1. Database\n- Path: `{db_path}`\n- Status: "
            f"{'✅ Connected' if db_exists else '❌ Missing'}"
        )

        if db_exists:
            count = await sqlite_storage.get_function_count()
            # New: Get count of assets that SHOULD be in Vector Store (have embeddings)
            db = await get_db_connection()
            sql = (
                "SELECT COUNT(*) FROM logichive_functions "
                "WHERE embedding IS NOT NULL AND embedding != 'null'"
            )
            async with db.execute(sql) as cursor:
                row = await cursor.fetchone()
                expected_count = row[0] if row else 0

            status.append(f"- Record Count: {count} ({expected_count} with embeddings)")

        # 2. Vector Store Check (ChromaDB)
        status.append(
            f"### 2. Vector Store (ChromaDB)\n- Path: `{CHROMA_DB_DIR}`"
        )

        # Check for memory sync (Silent check for initialization)
        if not vector_manager._initialized:
            status.append("- **Status**: 💤 Uninitialized (Will load on first search)")
        else:
            health = await vector_manager.check_health()
            if health["status"] == "Healthy":
                idx_size = health["details"]["total"]
                if idx_size != expected_count:
                    status.append(
                        f"- **Desync Detected**: DB({expected_count} verified) vs "
                        f"ChromaDB({idx_size}). Rebuild recommended."
                    )
                else:
                    status.append(f"- Sync Status: ✅ Optimal ({idx_size} vectors in collection)")
            else:
                status.append(f"- **Status**: ❌ Error: {health['message']}")

        # 3. Environment Pool Check
        from core.execution.pool import PoolManager

        pool = PoolManager.get_instance()
        status.append(
            f"### 3. Environment Pool\n- Base Dir: `{pool.base_dir}`\n- GPU Available: "
            f"{'✅' if pool.has_gpu else '❌'}"
        )

        return "\n".join(status)
    except Exception as e:
        import traceback

        return f"Integrity Check Failed: {str(e)}\n\n{traceback.format_exc()}"


@mcp.tool()
@trace_execution
async def get_verification_status(
    name: str, project: str = "default", wait_for_previous: bool = False
):
    """
    Checks the progress and detailed report of a background verification task.
    Use this to see if a recently saved function passed the Quality Gate.
    """
    logger.info(f"[TRACE] MCP: Tool 'get_verification_status' called for '{name}'")
    try:
        f_data = await do_get_verification_status(name, project=project)
        if f_data.get("status") == "not_found":
            return f_data["message"]

        status = f_data.get("status", "unknown")
        report = f_data.get("report")

        md = f"### Verification Status: {name}\n"
        md += f"- **Current Status**: {status.upper()}\n"
        md += _get_status_description(status)

        if report:
            md += "\n\n#### Detailed Report:\n"
            md += _format_report(report)

        return md
    except Exception as e:
        return f"Error retrieving status: {str(e)}"


@mcp.tool()
@trace_execution
async def rebuild_index(wait_for_previous: bool = False) -> str:
    """
    Forcefully rebuilds the FAISS vector index from all embeddings stored in the database.
    Use this if 'check_integrity' reports a desync between DB and Vector Store.
    """

    try:
        logger.info("[TRACE] MCP: Tool 'rebuild_index' called.")
        await vector_manager.rebuild_index()
        return "Vector index has been successfully rebuilt from database records."
    except Exception as e:
        logger.error(f"MCP Server: Error in rebuild_index: {e}")
        return f"LogicHive Error: Failed to rebuild index. Detail: {str(e)}"


def run_server():
    import uvicorn

    from core import __version__
    from core.config import validate_config_lazy

    # --- MONKEYPATCH UVICORN ---
    # Uvicorn's Server.startup calls sys.exit(1) directly on socket errors.
    # We override this to raise an exception instead, so we can handle it and wait_on_error.
    original_startup = uvicorn.Server.startup

    async def resilient_startup(self, sockets=None):
        try:
            await original_startup(self, sockets=sockets)
        except SystemExit as e:
            # If uvicorn tried to exit, it's likely a bind error (OSError)
            # Re-raise as OSError so our outer block can catch it
            if not self.started:
                raise OSError(10048, "Port binding failed (detected via SystemExit)") from e
            raise

    uvicorn.Server.startup = resilient_startup
    # ---------------------------

    # Use a loop to allow retries or port changes without restarting the process
    current_port = core.config.PORT
    while True:
        try:
            logger.debug(f"Starting server iteration on port {current_port}")
            if not os.environ.get("LOGICHIVE_TESTING"):
                # Improved configuration validation (User Request)
                is_valid, error_msg, config_path = validate_config_lazy()
                if not is_valid:
                    logger.error("Configuration validation failed")
                    logger.error(f"\n[!] CONFIGURATION INCOMPLETE: {error_msg}")
                    # ... (rest of logging)
                    wait_on_error()
                    sys.exit(1)

            # Apply settings
            host_val = core.config.HOST

            # Start network listeners
            logger.info("=" * 60)
            logger.info(f"Starting LogicHive Hub (v{__version__})")

            # Show active LLM configuration
            llm_provider = core.config.MODEL_TYPE.lower()
            if llm_provider == "gemini":
                llm_model = core.config.GEMINI_MODEL
            else:
                llm_model = core.config.OLLAMA_MODEL
            logger.info(f"LLM Provider: {llm_provider.upper()} ({llm_model})")

            # Show active Embedding configuration
            emb_provider = core.config.EMBEDDING_PROVIDER.lower()
            if emb_provider == "gemini":
                emb_model = core.config.EMBEDDING_MODEL_ID
            elif emb_provider == "fastembed":
                emb_model = core.config.FASTEMBED_MODEL
            else:
                emb_model = core.config.OLLAMA_EMBEDDING_MODEL
            logger.info(f"Embedding   : {emb_provider.upper()} ({emb_model})")

            logger.info(f"Network     : {host_val}:{current_port}")

            if host_val == "0.0.0.0":
                logger.warning("LAN SHARING IS ENABLED (0.0.0.0)")
                logger.warning("This server is accessible from other computers on your network.")

            # Create the app instance using Streamable HTTP with our middleware
            try:
                cors_middleware = Middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                    expose_headers=["*"],
                )
                app = mcp.http_app(transport="streamable-http", middleware=[cors_middleware])
                logger.debug("FastMCP HTTP app created with CORS middleware")
            except Exception as e:
                logger.error(f"Failed to create MCP app: {e}", exc_info=True)
                raise

            # ... (Inform user section)
            import uvicorn

            log_level = fastmcp.settings.log_level.lower()
            logger.info(f"Starting uvicorn with log_level: {log_level}")

            # Start the server
            uvicorn.run(app, host=host_val, port=current_port, log_level=log_level)

            break  # Success!

        except OSError as e:
            if e.errno == 10048 or "10048" in str(e):
                logger.error(f"Network bind error on port {current_port}: {e}")
                current_port = core.network.handle_port_conflict(current_port, host_val)
                continue
            raise

        except Exception as e:
            logger.critical(f"LogicHive MCP Server crashed unexpectedly: {e}")
            logger.exception("Fatal Traceback:")
            wait_on_error()
            sys.exit(1)


if __name__ == "__main__":
    run_server()
