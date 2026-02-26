import argparse
import json
import logging
import os
import sys
import ctypes
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from core.config import TRANSPORT
from edge.orchestrator import (
    do_save_impl,
    do_search_impl,
    do_get_impl,
    do_get_details_impl,
    do_delete_impl,
    do_list_impl,
    do_smart_get_impl,
)


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


# Initialize FastMCP
mcp = FastMCP("LogicHive", dependencies=["duckdb", "fastembed"])

# ----------------------------------------------------------------------
# MCP Tools (Direct Local Execution)
# ----------------------------------------------------------------------


@mcp.tool()
def list_functions(limit: int = 100) -> list[dict]:
    """Lists all stored functions from the local store."""
    return do_list_impl(limit=limit)


@mcp.tool()
def search_functions(query: str, limit: int = 5) -> list[dict]:
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
    tags: list[str] = [],
    dependencies: list[str] = [],
    test_cases: list[dict] = [],
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
def get_function_details(name: str) -> dict:
    """Retrieves full metadata for a local function."""
    return do_get_details_impl(name=name)


@mcp.tool()
def smart_search_and_get(query: str, target_dir: str = "./") -> dict:
    """
    [PRIMARY AI PROTOCOL] Intent-based Search -> Selection -> Injection.
    Uses local search + Hub-based reranking.
    """
    return do_smart_get_impl(query=query, target_dir=target_dir)


def main():
    """Entry point for the Edge MCP server."""
    is_frozen = getattr(sys, "frozen", False)

    # In frozen mode, sys.executable is the path to the EXE.
    # In script mode, __file__ is the path to the script.
    if is_frozen:
        project_root = Path(sys.executable).parent.resolve()
    else:
        project_root = Path(__file__).parent.parent.parent.resolve()

    # Initialize logging
    setup_logging(is_frozen, project_root)

    try:
        logging.info(f"LogicHive starting... (Frozen: {is_frozen})")
        logging.info(f"Project Root: {project_root}")

        parser = argparse.ArgumentParser(description="LogicHive Edge MCP Server")
        parser.add_argument(
            "--generate-mcp-config",
            action="store_true",
            help="Generate Cursor/Gemini Desktop config",
        )
        args = parser.parse_args()

        config_file = project_root / "mcp_config_logic_hive.json"
        config = {}
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load config: {e}")

        # --- LICENSE CONSENT LOGIC ---
        if is_frozen and os.name == "nt" and not config.get("license_consent"):
            consent_text = (
                "LogicHive utilizes 'LogicHive-Storage' (a public GitHub repository) as a global shared database for the community.\n\n"
                "By using this software for free during the MVP phase, you agree that any functions you register/save will be "
                "published under the MIT License and shared with the global community.\n\n"
                "Do you agree to these terms?"
            )
            # MB_YESNO = 0x4, MB_ICONQUESTION = 0x20, IDYES = 6
            res = ctypes.windll.user32.MessageBoxW(
                0, consent_text, "LogicHive License Consent", 0x4 | 0x20
            )
            if res != 6:
                logging.info("User declined license consent. Exiting.")
                sys.exit(0)

            config["license_consent"] = True
            try:
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                logging.info("License consent saved to config.")
            except Exception as e:
                logging.error(f"Failed to save consent to config: {e}")

        # AUTO-SETUP logic: If running as EXE and config is missing, generate it first.
        if is_frozen and not config_file.exists() or args.generate_mcp_config:
            from core.setup import generate_config

            generate_config(is_frozen=is_frozen)

            if is_frozen and os.name == "nt":
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"Setup Complete!\n\nMCP configuration has been generated at:\n{config_file}\n\nPlease add this to Cursor/Gemini Desktop settings.",
                    "LogicHive Setup",
                    0x40,
                )

            if args.generate_mcp_config:
                return

        logging.info("Starting FastMCP server loop...")
        mcp.run(transport=TRANSPORT)

    except Exception as e:
        logging.exception("A fatal error occurred during execution:")
        print(f"\n[FATAL ERROR] {e}")
        print("\n" + "=" * 50)
        print(
            "The application crashed. Please check 'logichive.log' in the EXE folder."
        )
        print("=" * 50)
        if is_frozen:
            input("\nPress ENTER to close this window...")
        sys.exit(1)


if __name__ == "__main__":
    main()
