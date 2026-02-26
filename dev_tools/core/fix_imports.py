import os

MAPPING = {
    # Core
    "mcp_core.core.config": "core.config",
    "mcp_core.core.security": "core.security",
    "mcp_core.core.database": "core.database",
    "mcp_core.engine.embedding": "core.embedding",
    "mcp_core.engine.sanitizer": "core.sanitizer",
    "mcp_core.engine.quality_gate": "core.quality",
    "mcp_core.auth": "core.auth",
    # Hub
    "mcp_core.infra.background_server": "hub.app",
    "mcp_core.engine.logic": "hub.orchestrator",
    "mcp_core.engine.router": "hub.router",
    "mcp_core.api": "hub.api",
    "mcp_core.infra.coordinator": "hub.coordinator",  # Adjust if moved to edge
    # Edge
    "mcp_core.server": "edge.mcp_server",
    "mcp_core.core.mcp_manager": "edge.manager",
    "mcp_core.engine.package_generator": "edge.generator",
    "mcp_core.engine.dependency_solver": "edge.solver",
    "mcp_core.engine.sync_engine": "edge.sync",
    "mcp_core.runtime": "edge.runtime",
    "mcp_core.engine.security_audit": "edge.audit",
    "mcp_core.core.vector_db": "edge.vector_db",
    "mcp_core.engine.worker": "edge.worker",
    "mcp_core.engine.cleanup": "edge.cleanup",
    "mcp_core.engine.triage": "edge.triage",
    "mcp_core.engine.popular_query_cache": "edge.cache",
}

# General sub-package fallback
FALLBACK = {
    "mcp_core.core": "core",
    "mcp_core.engine": "edge",  # Most engine files went to edge
    "mcp_core.infra": "hub",
    "mcp_core.server": "edge.transport",
}


def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = content
    # Order matters: Specific mappings first
    for old, new in MAPPING.items():
        new_content = new_content.replace(f"from {old}", f"from {new}")
        new_content = new_content.replace(f"import {old}", f"import {new}")
        new_content = new_content.replace(f"{old}.", f"{new}.")

    # Fallback mappings
    for old, new in FALLBACK.items():
        new_content = new_content.replace(f"from {old}", f"from {new}")
        new_content = new_content.replace(f"import {old}", f"import {new}")
        # Note: Avoid replacing . in middle of words if possible

    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed: {path}")


def main():
    dirs_to_fix = [
        "backend",
        "dev_tools/tests",
        "hub",
        "edge",
        "core",
    ]  # Cover all new roots
    for base_dir in dirs_to_fix:
        if not os.path.exists(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".py"):
                    fix_file(os.path.join(root, file))


if __name__ == "__main__":
    main()
