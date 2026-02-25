import json
import os
import sys
from pathlib import Path


def generate_config(is_frozen=False):
    """Generates a zero-config MCP configuration JSON and injects it into known environments."""
    print("--- LogicHive: Zero-Config Setup ---")

    if is_frozen:
        # Running inside the bundled EXE
        exe_path = Path(sys.executable).absolute()
        project_root = exe_path.parent
        command = str(exe_path).replace("\\", "/")
        args = []
        python_path = ""
    else:
        # Running in development
        project_root = Path(__file__).parent.parent.parent.absolute()
        command = "uv"
        args = [
            "run",
            "--with",
            "duckdb",
            "--with",
            "fastmcp",
            "python",
            "-m",
            "edge.mcp_server",
        ]
        python_path = str(project_root / "backend").replace("\\", "/")

    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    server_config = {
        "command": command,
        "args": args,
        "env": {
            "FS_DATA_DIR": str(data_dir).replace("\\", "/"),
        },
    }

    if python_path:
        server_config["env"]["PYTHONPATH"] = python_path

    # 1. Generate local standalone config
    standalone_config = {"mcpServers": {"logic-hive": server_config}}

    config_output = project_root / "mcp_config_logic_hive.json"
    with open(config_output, "w", encoding="utf-8") as f:
        json.dump(standalone_config, f, indent=2)
    print(f"[SUCCESS] Local config generated: {config_output}")

    # 2. AUTO-INJECTION logic (The "Just Do It" Strategy)
    inject_targets = [
        # Cursor (Standard Windows path)
        Path(os.getenv("APPDATA", ""))
        / "Cursor/User/globalStorage/heavy.cursor.cursor/mcp_config.json",
        # Gemini Desktop / Antigravity (Detected in metadata)
        Path.home() / ".gemini/antigravity/mcp_config.json",
    ]

    injected_any = False
    for target in inject_targets:
        if target.exists():
            try:
                print(f"[INFO] Detecting {target.parent.parent.name} configuration...")
                with open(target, "r", encoding="utf-8") as f:
                    content = json.load(f)

                if "mcpServers" not in content:
                    content["mcpServers"] = {}

                # Update or Add the server
                content["mcpServers"]["logic-hive"] = server_config

                with open(target, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2)

                print(f"[SUCCESS] Automatically injected into: {target}")
                injected_any = True
            except Exception as e:
                print(f"[WARNING] Injection failed for {target}: {e}")

    if not injected_any:
        print(
            "\n[NOTE] No active MCP environments (Cursor/Gemini) were auto-detected for injection."
        )
        print(
            "Please manually add the contents of 'mcp_config_logic_hive.json' to your editor settings."
        )
    else:
        print(
            "\n[READY] LogicHive is now registered! Please restart your AI Agent (Cursor/Gemini) to apply changes."
        )

    # 3. Development Bonus
    if os.name == "nt" and not is_frozen:
        bat_path = project_root / "start_mcp.bat"
        with open(bat_path, "w") as f:
            f.write("@echo off\n")
            f.write(f"set PYTHONPATH={python_path}\n")
            f.write("uv run --with duckdb --with fastmcp python -m edge.mcp_server\n")
        print(f"[BONUS] Windows startup script created: {bat_path.name}")
