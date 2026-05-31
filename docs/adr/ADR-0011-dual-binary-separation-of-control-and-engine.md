# ADR-0011: Separation of Engine (MCP) and Control (Settings GUI)

- **Date**: 2026-05-29
- **Status**: Accepted
- **Deciders**: Gemini CLI, ayato-labs

## Context
LogicHive currently integrates both the MCP server logic and the initial configuration/setup flows into a single entry point (`mcp_server.py`). As the system matures, this monolithic approach presents several challenges:
1.  **Stability**: A crash in the configuration UI or validation logic could potentially impact the running MCP server.
2.  **Security**: The core engine requires "Read" access to configuration, but currently also handles "Write" operations during setup. This violates the principle of least privilege.
3.  **User Experience**: Users (especially non-developers) benefit from a persistent, user-friendly GUI to manage API keys, monitor system health, and perform manual integrity checks without interrupting the background engine.
4.  **Binary Size**: Bundling heavy GUI libraries into the core engine increases the distribution size for the OCI container and headless environments.

## Decision
We will split the application into two distinct binaries:

1.  **`logichive-hub.exe` (The Engine / Hub)**:
    -   **Purpose**: Headless MCP server (SSE transport).
    -   **Permissions**: Read-only access to configuration (`.env` / `config.env`).
    -   **Focus**: Maximum uptime, low latency, and stability.
2.  **`logichive-settings.exe` (The Control / Dashboard)**:
    -   **Purpose**: GUI application for configuration management and system diagnostics.
    -   **Permissions**: Read/Write access to the configuration directory (`C:\.logichive` or `~/.logichive`).
    -   **Features**: API key validation, health monitoring (Integrity Report), and log viewing.

Both binaries will share the same persistent storage directory for configuration and data to ensure seamless coordination.

## Consequences

### Positive
-   **Enhanced Stability**: The background service is isolated from configuration UI errors.
-   **Improved Security**: Proper privilege separation (Read vs. Write).
-   **Superior UX**: Professional dashboard for monitoring and settings.
-   **Optimized Distribution**: GUI libraries are only required for the control binary.

### Negative / Risks
-   **Build Complexity**: Managing two separate build targets in the CI/CD pipeline.
-   **Coordination**: Ensuring both apps are synchronized on the configuration schema.

## References
- Issue: #N/A (Separation of Concerns)
- ADR-002: Dual Distribution
- ADR-005: Configuration Resolution Strategy
