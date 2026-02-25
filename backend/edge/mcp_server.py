import argparse
import json
import logging
import os
import sys
import ctypes
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from core.config import TRANSPORT, SETTINGS_PATH

def setup_logging(is_frozen: bool, project_root: Path):
    """Configures logging to both console and file."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Base configuration for console
    logging.basicConfig(level=logging.INFO, format=log_format)
    
    if is_frozen:
        log_file = project_root / "logichive.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
        logging.info(f"Logging initialized. Log file: {log_file}")

# Import local stateful orchestrator
from edge.orchestrator import (
    do_save_impl,
    do_search_impl,
    do_get_impl,
    do_get_details_impl,
    do_delete_impl,
    do_smart_get_impl,
)

# Initialize FastMCP
mcp = FastMCP("function-store", dependencies=["duckdb", "fastembed"])

# ----------------------------------------------------------------------
# MCP Tools (Direct Local Execution)
# ----------------------------------------------------------------------

@mcp.tool()
def search_functions(query: str, limit: int = 5) -> List[Dict]:
    """
    [EXPLORATION TOOL] Catalog search for reusable functions.
    Searches local DuckDB/Qdrant.
    """
    return do_search_impl(query=query, limit=limit)

@mcp.tool()
def save_function(
    name: str,
    code: str,
    description: str = "",
    tags: List[str] = [],
    dependencies: List[str] = [],
    test_cases: List[Dict] = [],
    skip_test: bool = False,
) -> str:
    """
    Saves or updates a Python function in the local persistent store.
    """
    return do_save_impl(
        asset_name=name,
        code=code,
        description=description,
        tags=tags,
        dependencies=dependencies,
        test_cases=test_cases,
        skip_test=skip_test,
    )

@mcp.tool()
def delete_function(name: str) -> str:
    """Permanently deletes a function from the local store."""
    return do_delete_impl(asset_name=name)

@mcp.tool()
def get_function(name: str, integrate_dependencies: bool = False) -> str:
    """Retrieves the raw source code of a specific function from local store."""
    return do_get_impl(asset_name=name, integrate_dependencies=integrate_dependencies)

@mcp.tool()
def get_function_details(name: str) -> Dict:
    """Retrieves full metadata for a local function."""
    return do_get_details_impl(name=name)

@mcp.tool()
def smart_search_and_get(query: str, target_dir: str = "./") -> Dict:
    """
    [PRIMARY AI PROTOCOL] Intent-based Search -> Selection -> Injection.
    Uses local search + Hub-based reranking.
    """
    return do_smart_get_impl(query=query, target_dir=target_dir)

def main():
    """Entry point for the Edge MCP server."""
    is_frozen = getattr(sys, "frozen", False)
    project_root = Path(sys.executable).parent if is_frozen else Path(__file__).parent.parent.parent
    
    # Initialize logging
    setup_logging(is_frozen, project_root)
    
    parser = argparse.ArgumentParser(description="LogicHive Edge MCP Server")
    parser.add_argument("--generate-mcp-config", action="store_true", help="Generate Cursor/Gemini Desktop config")
    args = parser.parse_args()

    config_file = project_root / "mcp_config_logic_hive.json"

    # AUTO-SETUP logic: If running as EXE and config is missing, generate it first.
    if is_frozen and not config_file.exists() or args.generate_mcp_config:
        from core.setup import generate_config
        generate_config(is_frozen=is_frozen)
        
        if is_frozen and os.name == "nt":
            ctypes.windll.user32.MessageBoxW(0, f"Setup Complete!\n\nMCP configuration has been generated at:\n{config_file}\n\nPlease add this to Cursor/Gemini Desktop settings.", "LogicHive Setup", 0x40)
        
        if args.generate_mcp_config:
            return

    mcp.run(transport=TRANSPORT)

if __name__ == "__main__":
    main()
