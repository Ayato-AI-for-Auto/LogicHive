# Copyright (C) 2026 ayato-labs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sqlite3
from contextlib import asynccontextmanager

from fastmcp import FastMCP

import orchestrator
from core.config import FAISS_INDEX_PATH, SQLITE_DB_PATH
from core.db import get_db_connection
from core.exceptions import LogicHiveError, SyntaxValidationError, ValidationError
from core.logging_config import get_logger
from core.tracer import trace_execution
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
    """Initializes and cleans up the background worker for environment pooling."""
    from core.execution.pool import PoolManager

    manager = PoolManager.get_instance()
    await manager.initialize()
    try:
        yield
    finally:
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
        wait_for_previous: Set to true to wait for all previously requested tools in this turn to complete before starting. Set to false (or omit) to run in parallel. Use true when this tool depends on the output of previous tools.
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

            # Check for Environment Drift
            drift_warning = ""
            stored_env = res.get("env_fingerprint")
            if stored_env:
                from core.system_info import SystemFingerprint

                if SystemFingerprint.compare(stored_env, SystemFingerprint.get_current()):
                    drift_warning = " [DRIFT]"

            md += f"- **{name}{drift_warning}** (Match: {sim:.2f}, Reliability: {rel:.1f}%)\n"
            if is_draft:
                md += "  - *NOTE: This is a generated draft. Refine and Save to verify.*\n"
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
        wait_for_previous: Set to true to wait for all previously requested tools in this turn to complete before starting. Set to false (or omit) to run in parallel. Use true when this tool depends on the output of previous tools.
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

        # Environment Drift Check
        drift_header = ""
        stored_env = f_data.get("env_fingerprint")
        if stored_env:
            from core.system_info import SystemFingerprint

            warning = SystemFingerprint.generate_warning_msg(stored_env)
            if warning:
                drift_header = f"> [!WARNING]\n> {warning.replace(chr(10), chr(10) + '> ')}\n\n"

        return f"**Function: {name}**\n\n{drift_header}{desc}\n\n**Tags:** {tags}\n**Dependencies:** {deps}\n\n```{lang}\n{code}\n```"
    except Exception as e:
        logger.error(f"MCP Server: Error in get_function: {e}")
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
        return (
            (
                f"Asset '{name}' (Project: {project}) has been accepted and saved with status 'pending'.\n"
                "Verification is running in the background. Use 'get_verification_status' to check progress."
            )
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
            "### ❌ IMMEDIATE REJECTION: Syntax Error",
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
        score = details.get("score", 0)
        reason = details.get("reason", str(e))
        eval_details = details.get("eval_details", {})

        # Build a helpful report
        report = [f"Quality Gate REJECTED: {reason}", f"Final Score: {score:.1f}/100"]

        if eval_details:
            report.append("\nBreakdown:")
            for tool_name, res in eval_details.items():
                tool_score = res.get("score", 0)
                tool_reason = res.get("reason", "N/A")
                report.append(f"- {tool_name}: {tool_score:.1f} ({tool_reason})")

                # Show traceback or stderr if available (Crucial for debugging)
                inner_details = res.get("details", {}) or {}
                if inner_details.get("traceback"):
                    report.append(f"  [TRACEBACK]\n{inner_details['traceback']}")
                elif inner_details.get("stderr"):
                    report.append(f"  [STDERR]\n{inner_details['stderr']}")

        return "\n".join(report)
    except LogicHiveError as e:
        return f"LogicHive SYSTEM ERROR: {str(e)}\n\n(This is likely a transient infrastructure issue, not a problem with your code. Please try again in a few moments.)"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"


@mcp.tool()
@trace_execution
async def debug_db(wait_for_previous: bool = False) -> str:
    """
    Debug tool to inspect LogicHive database configuration and table structure.

    Args:
        wait_for_previous: Set to true to wait for all previously requested tools in this turn to complete before starting. Set to false (or omit) to run in parallel. Use true when this tool depends on the output of previous tools.
    """

    from core.config import SQLITE_DB_PATH

    status = [f"SQLITE_DB_PATH: {SQLITE_DB_PATH}"]
    status.append(f"Exists: {os.path.exists(SQLITE_DB_PATH)}")

    if os.path.exists(SQLITE_DB_PATH):
        try:
            status.append(f"Size: {os.path.getsize(SQLITE_DB_PATH)} bytes")
            conn = sqlite3.connect(SQLITE_DB_PATH)
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
    The function is archived in the backup repository for safety.

    Args:
        name: The case-sensitive name of the function to delete.
        project: The project namespace (defaults to 'default').
        wait_for_previous: Set to true to wait for all previously requested tools in this turn to complete before starting. Set to false (or omit) to run in parallel. Use true when this tool depends on the output of previous tools.
    """
    success = await do_delete_async(name, project=project)
    if success:
        return f"Successfully deleted and archived function '{name}' in project '{project}'."
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
        wait_for_previous: Set to true to wait for all previously requested tools in this turn to complete before starting. Set to false (or omit) to run in parallel. Use true when this tool depends on the output of previous tools.
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
        wait_for_previous: Set to true to wait for all previously requested tools in this turn to complete before starting. Set to false (or omit) to run in parallel. Use true when this tool depends on the output of previous tools.
    """

    from storage.vector_store import vector_manager

    status = ["## LogicHive Integrity Report\n"]

    try:
        # 1. DB Check
        db_exists = os.path.exists(SQLITE_DB_PATH)
        status.append(
            f"### 1. Database\n- Path: `{SQLITE_DB_PATH}`\n- Status: {'✅ Connected' if db_exists else '❌ Missing'}"
        )

        if db_exists:
            count = await sqlite_storage.get_function_count()
            # New: Get count of assets that SHOULD be in FAISS (have embeddings)
            db = await get_db_connection()
            async with db.execute(
                "SELECT COUNT(*) FROM logichive_functions WHERE embedding IS NOT NULL AND embedding != 'null'"
            ) as cursor:
                row = await cursor.fetchone()
                expected_count = row[0] if row else 0

            status.append(f"- Record Count: {count} ({expected_count} with embeddings)")

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
                if idx_size != expected_count:
                    status.append(
                        f"- **Desync Detected**: DB({expected_count} verified) vs FAISS-Memory({idx_size}). Rebuild recommended."
                    )
                else:
                    status.append(f"- Sync Status: ✅ Optimal ({idx_size} vectors in memory)")

        # 3. Environment Pool Check
        from core.execution.pool import PoolManager

        pool = PoolManager.get_instance()
        status.append(
            f"### 3. Environment Pool\n- Base Dir: `{pool.base_dir}`\n- GPU Available: {'✅' if pool.has_gpu else '❌'}"
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


def _get_status_description(status):
    mapping = {
        "verified": "Quality Gate passed. Asset is active in the vault.\n",
        "pending": "Verification is still in progress. Please check back shortly.\n",
        "failed": "Quality Gate rejected the asset. Review the report below for details.\n",
        "error": "A system error occurred during verification. Infrastructure might be unstable.\n",
    }
    return mapping.get(status, "")


def _format_report(report):
    if not isinstance(report, dict):
        return f"```json\n{report}\n```"

    if "error" in report:
        return f"**Error Details**: {report['error']}\n"

    if "reason" in report:
        md = f"- **Reason**: {report.get('reason', 'N/A')}\n"
        details = report.get("details", {})
        for tool, res in details.items():
            md += f"- **{tool.title()}**: {res.get('score', 0):.1f} ({res.get('reason', 'N/A')})\n"
        return md

    import json

    return f"```json\n{json.dumps(report, indent=2)}\n```"


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


if __name__ == "__main__":
    import sys
    import traceback
    import uvicorn
    import psutil
    import socket

    from core import __version__
    from core.config import HOST, PORT, save_config, validate_config_lazy
    from core.system_info import SystemFingerprint

    def wait_on_error():
        """Prevents the terminal window from closing immediately in frozen mode."""
        if getattr(sys, "frozen", False):
            print("\n" + "=" * 60)
            input("Press Enter to exit...")

    def get_conflicting_process(port: int):
        """Identifies the process currently using the specified port."""
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return psutil.Process(conn.pid)
        except Exception:
            pass
        return None

    def find_available_port(start_port: int, host: str = "0.0.0.0") -> int:
        """Finds the first available port starting from start_port."""
        port = start_port
        while port < 65535:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((host, port))
                    return port
                except OSError:
                    port += 1
        return start_port

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
    current_port = PORT
    while True:
        try:
            # Improved configuration validation (User Request)
            is_valid, error_msg, config_path = validate_config_lazy()
            if not is_valid:
                # Interactive Setup Flow
                print("\n" + "=" * 60)
                print(f"Welcome to LogicHive MCP (v{__version__})!")
                print("It looks like this is your first run or your configuration is incomplete.")
                print("=" * 60)
                
                print("\nStep 1: Choose your AI & Embedding Provider")
                print("  [1] Ollama & Fastembed (Local-first, No API Key needed) - DEFAULT")
                print("  [2] Google Gemini (Cloud-based, requires API Key)")
                
                choice = input("\nSelect [1] or [2] (default 1): ").strip()
                
                if choice == "2":
                    print("\nStep 2: Configure Gemini")
                    key = input("Enter your GEMINI_API_KEY: ").strip()
                    if key:
                        save_config({
                            "MODEL_TYPE": "gemini",
                            "EMBEDDING_PROVIDER": "gemini",
                            "GEMINI_API_KEY": key
                        })
                        print(f"[SUCCESS] Configuration saved to {config_path}")
                    else:
                        print("[WARNING] No key provided. Gemini mode will require manual .env editing.")
                else:
                    # Default: Ollama & Fastembed
                    save_config({
                        "MODEL_TYPE": "ollama",
                        "EMBEDDING_PROVIDER": "ollama"
                    })
                    print("[SUCCESS] Local-first mode (Ollama/Fastembed) selected.")
                    print("[NOTE] Ensure Ollama is installed and running (https://ollama.com)")

                # Re-verify after setup
                is_valid, error_msg, _ = validate_config_lazy()
                
                if not is_valid:
                    print(f"\n[!] CONFIGURATION STILL INCOMPLETE: {error_msg}")
                    print(f"Please edit your configuration file manually at:\n  {config_path}")
                    wait_on_error()
                    sys.exit(1)

            # Improved logging for discoverability (User Request)
            base_url = f"http://{HOST}:{current_port}/sse"
            logger.info(f"Starting LogicHive MCP Server (v{__version__}) on {base_url}")

            if HOST == "0.0.0.0":
                ips = SystemFingerprint.get_local_ips()
                logger.info("Server is accessible at:")
                for ip in ips:
                    logger.info(f"  > http://{ip}:{current_port}/sse")

            mcp.run(transport="sse", host=HOST, port=current_port)
            break # Success!

        except OSError as e:
            if e.errno == 10048 or "10048" in str(e):
                print(f"\n[!] NETWORK ERROR: Port {current_port} is already in use.")
                
                # Diagnostics
                proc = get_conflicting_process(current_port)
                if proc:
                    print(f"Conflicting process found: {proc.name()} (PID: {proc.pid})")
                
                print("\nHow would you like to resolve this?")
                print(f"  [R] Retry (tries {current_port} again)")
                if proc:
                    print(f"  [K] Kill conflicting process ({proc.name()}) and start")
                print(f"  [A] Auto-find an available port")
                print("  [E] Exit")
                
                res = input("\nSelect [R/K/A/E]: ").strip().upper()
                
                if res == "R":
                    continue
                elif res == "K" and proc:
                    try:
                        print(f"Terminating {proc.name()}...")
                        proc.terminate()
                        proc.wait(timeout=5)
                        continue
                    except Exception as kill_err:
                        print(f"[ERROR] Could not terminate process: {kill_err}")
                elif res == "A":
                    new_port = find_available_port(current_port + 1, HOST)
                    print(f"\nFound available port: {new_port}")
                    ans = input(f"Use port {new_port} and update your .env? [Y/n]: ").strip().lower()
                    if ans != "n":
                        save_config({"PORT": new_port})
                        current_port = new_port
                    continue
                else:
                    wait_on_error()
                    sys.exit(1)
            
            print(f"\n[FATAL OS ERROR]: {e}")
            traceback.print_exc()
            wait_on_error()
            sys.exit(1)

        except Exception as e:
            print(f"\n[FATAL ERROR] LogicHive MCP Server failed to start:\n{e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            wait_on_error()
            sys.exit(1)
