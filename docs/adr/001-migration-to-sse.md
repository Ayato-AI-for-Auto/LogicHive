# ADR-001: Migration from Stdio to Streamable HTTP (SSE)

## Status
Accepted

## Context
LogicHive originally used the standard input/output (Stdio) transport for the Model Context Protocol (MCP). While simple, this restricted each LogicHive instance to a single local client process (e.g., one Cursor instance). 

## Decision
We decided to migrate to **Streamable HTTP (SSE)** as the primary transport layer.

## Consequences
- **Multi-client support**: Multiple AI agents across a network can now connect to a single LogicHive hub.
- **Centralization**: A single "Central Hub" (e.g., a Windows server) can serve an entire team of Mac/Linux users.
- **Observability**: Standard HTTP debugging tools can be used to monitor the event stream.
- **Configuration Change**: AI clients must now connect via a URL (`/sse`) instead of a local command execution.
