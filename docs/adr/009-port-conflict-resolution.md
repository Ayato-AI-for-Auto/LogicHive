# ADR-009: Interactive Port Conflict Resolution and Process Recovery

- **Date**: 2026-05-27
- **Status**: Accepted
- **Deciders**: Gemini CLI (Agent), ayato-labs (User)

## Context
LogicHive MCP server defaults to port `10880`. If another instance is running or another application occupies this port, the server fails with `OSError: [Errno 10048]`. Currently, the application provides an error message and waits for the user to exit. This creates friction, especially for non-technical users who may have "ghost" processes running in the background or multiple windows open.

## Decision
We will implement an interactive conflict resolution mechanism in the server startup logic.

Key features:
1.  **Process Detection**: Use `psutil` to identify the Process ID (PID) and Name of the application currently occupying the target port.
2.  **Interactive Recovery Menu**: Present the user with actionable choices when a conflict is detected:
    -   **Retry**: Re-attempt binding (user manually cleared the port).
    -   **Kill**: Programmatically terminate the conflicting process (privileged action).
    -   **Auto-find**: Search for the first available port incrementing from the target (e.g., 10881, 10882).
3.  **Startup Loop**: Wrap the server initialization in a loop to allow these transitions without restarting the entire application executable.
4.  **Configuration Persistence**: If the user chooses a new port via "Auto-find", the system will offer to save this change to the `.env` file permanently.

## Consequences
### Positive
- **Reduced Friction**: Users can resolve common "address already in use" errors without opening Task Manager or editing text files manually.
- **Improved Visibility**: Explicitly showing *what* is using the port (e.g., "Conflict: LogicHive-MCP.exe (PID 1234)") provides immediate clarity.
- **Resilience**: The server becomes much harder to "break" during routine usage or development restarts.

### Negative / Risks
- **Termination Risk**: The "Kill" option is powerful and could potentially close an unrelated application if the user isn't careful (though highly unlikely for port 10880).
- **Dependency**: Adds a hard dependency on `psutil` (already present in the project).

## References
- Error: [Errno 10048]
- Tool: psutil
