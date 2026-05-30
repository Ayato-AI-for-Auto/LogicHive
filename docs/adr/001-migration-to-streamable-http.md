# ADR-001: Migration from Stdio to Streamable HTTP

- **Date**: 2024-11-20 (Originally), 2026-05-30 (Revised)
- **Status**: Accepted
- **Deciders**: ayato-labs, Gemini CLI

## Context
LogicHive originally used the standard input/output (Stdio) transport for the Model Context Protocol (MCP). While simple, this restricted each LogicHive instance to a single local client process. To support modern, networked, and containerized AI environments, a more robust HTTP-based transport is required.

In 2026, the industry has standardized on **Streamable HTTP** as the successor to the legacy SSE (Server-Sent Events) transport. Streamable HTTP provides a single-endpoint, bidirectional communication channel that is more resilient to infrastructure timeouts and corporate proxies.

## Decision
We decided to adopt **Streamable HTTP** as the primary transport layer for LogicHive.

### Implementation Details:
- **FastAPI Wrapper**: To handle modern browser-based client requirements (like Cline/Cursor), the server is wrapped in FastAPI with explicit `CORSMiddleware`.
- **Endpoint**: The server listens on a single Streamable HTTP endpoint (defaulting to `/mcp`).
- **CORS Handling**: Full preflight (`OPTIONS`) support is provided, and all response headers are explicitly exposed (`expose_headers=["*"]`). This is critical for webview-based clients to read the MCP session ID from the server's response.

## Consequences
- **Multi-client support**: Multiple AI agents across a network can connect to a single LogicHive hub.
- **Robustness**: Bidirectional streaming over a single POST/GET cycle reduces connection drops.
- **2026 Standard Compliance**: Full compatibility with Cline (v3.0+), Cursor, and Claude Desktop's modern connection handlers.

## References (2026 Research)
- **Cline Documentation (May 2026)**: Confirms Streamable HTTP as the "Recommended" transport for remote MCP servers.
  - [https://cline.bot/docs/mcp/transports](https://cline.bot/docs/mcp/transports)
- **Claude Desktop Config Spec**: Details on supporting both legacy SSE and modern Streamable HTTP.
  - [https://docs.anthropic.com/en/docs/agents-and-tools/mcp/transports](https://docs.anthropic.com/en/docs/agents-and-tools/mcp/transports)
- **MCP Spec (March 2025 Update)**: The foundational protocol change that consolidated bidirectional streams into Streamable HTTP.
  - [https://modelcontextprotocol.io/spec/transports#streamable-http](https://modelcontextprotocol.io/spec/transports#streamable-http)
- **Infrastructure Guide**: Explains why Streamable HTTP is superior for load balancers compared to SSE.
  - [https://www.cloudflare.com/learning/mcp/streamable-http-vs-sse/](https://www.cloudflare.com/learning/mcp/streamable-http-vs-sse/)
