# ADR-0010: Wi-Fi/LAN Sharing and Default Secure Host Configuration

- **Date**: 2026-05-27 (Originally), 2026-05-30 (Revised)
- **Status**: Accepted
- **Deciders**: ayato-labs, Gemini CLI

## Context
LogicHive is being distributed as a standalone `.exe` executable for team-wide use.
Previously, the default host configuration was set to `0.0.0.0`, listening on all interfaces. However, because FastMCP/MCP does not feature built-in authentication mechanisms, this configuration poses a Remote Code Execution (RCE) security risk to users on untrusted public Wi-Fi networks.

Furthermore, relying on raw IP addresses (e.g., `192.168.x.x`) for team sharing is unstable due to DHCP lease expiration and network reconnects. A more resilient discovery mechanism is needed for 2026-standard professional environments.

## Decision
1. **Secure by Default**: Set the default `HOST` setting to `127.0.0.1` (Local Only).
2. **mDNS (.local) Priority**: When LAN sharing (`0.0.0.0`) is enabled, the primary connection URL promoted to team members shall be host-based: `http://<hostname>.local:<port>/mcp`. 
3. **Multicast DNS Adoption**: Leverage mDNS (Bonjour) for zero-config name resolution. This ensures team members can maintain a stable connection even if the server's IP address changes via DHCP.
4. **Streamable HTTP Integration**: All connection URLs must use the modern `/mcp` endpoint as defined in ADR-001.

## Consequences
### Positive
- **Stability**: Connections survive IP changes; no need for team members to reconfigure their AI clients (Cline/Cursor).
- **Default Security**: Protection against unauthorized access on public networks.
- **Improved UX**: Users communicate using human-readable names rather than cryptic numeric IPs.

### Negative / Risks
- **Network Constraints**: Requires mDNS traffic (UDP 5353) to be allowed on the router and OS firewall.

## References
- Issue: #N / PR: #N
