# ADR-0027: MCP Server Module Decomposition

- **Date**: 2026-06-12
- **Status**: Accepted
- **Deciders**: Antigravity

## Context
`mcp_server.py` is the entry point for the LogicHive MCP server. Over time, it has grown to approximately 900 lines of code. It contains multiple distinct responsibilities:
1. Lifespan management (startup/shutdown hooks)
2. Background periodic vulnerability scanning loop
3. Output formatters for errors and reports
4. Network diagnostics (finding free ports, checking process conflicts)
5. Port recovery loop in case of address binding conflicts
6. FastMCP tool registrations and handler functions

Having all these responsibilities in a single file violates the Single Responsibility Principle (SRP) and makes testing/maintenance difficult. However, `mcp_server.py` is also hard-coded as the entry point in several scripts, the build configuration, processes checks, and many unit/integration tests import directly from it.

## Decision
We will refactor `mcp_server.py` using **Strategy B**:
- Retain `mcp_server.py` as the entry point and the place where FastMCP tool registration occurs.
- Extract the business logic into separate modular components under the `core/` package:
  - `core/vulnerability/scanner.py` for vulnerability scanning background tasks.
  - `core/formatters.py` for error and report formatting.
  - `core/network/diagnostics.py` for network and process conflict diagnostics.
  - `core/network/recovery.py` for the port conflict recovery flow.
- Maintain backward compatibility in `mcp_server.py` by importing and re-exporting the extracted functions so that external callers, configuration files, and test mocks do not break.

## Consequences
### Positive
- Separation of concerns is achieved without breaking existing contracts.
- Size of `mcp_server.py` is reduced by over 60% (from ~900 lines to ~350 lines).
- Modularity improves readability and facilitates unit testing.
- No need to update the PyInstaller/packaging config or external startup/cleanup scripts.

### Negative / Risks
- Potential risk of introducing import cycle dependencies if not carefully managed.
- Tests that mock functions on `mcp_server` (e.g., using `unittest.mock.patch("mcp_server.get_conflicting_process")`) must still work via the re-exported functions.

## References
- Issue: #19
- ADR: ADR-0009-port-conflict-resolution.md, ADR-0024-in-memory-periodic-vulnerability-scanning.md
