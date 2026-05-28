# ADR-0010: Wi-Fi/LAN Sharing and Default Secure Host Configuration

- **Date**: 2026-05-27
- **Status**: Proposed
- **Deciders**: ayato-labs (Human), Antigravity (AI Agent)

## Context
LogicHive is being distributed as a standalone `.exe` executable for team-wide use.
Previously, the default host configuration was set to `0.0.0.0`, listening on all interfaces. However, because FastMCP/MCP does not feature built-in authentication mechanisms, this configuration poses a Remote Code Execution (RCE) security risk to users on untrusted public Wi-Fi networks.
At the same time, teams working on the same local network (Wi-Fi/LAN) require a way to access the host's server without constantly checking and updating changing IP addresses.

## Decision
1. **Secure by Default**: Set the default `HOST` setting to `127.0.0.1` (Local Only) instead of `0.0.0.0` in the configuration template.
2. **Onboarding Host Configuration**: Extend the setup wizard on first run to prompt the user to choose their sharing preference:
   - Option 1: Local Only (`127.0.0.1`) - Default and Recommended.
   - Option 2: Wi-Fi/LAN Share (`0.0.0.0`) - Team Sharing.
3. **mDNS Auto-Discovery & Security Warning**: When starting in shared mode (`0.0.0.0`), dynamically query the machine's hostname (`socket.gethostname().lower()`) and output the team connection URL using the mDNS `.local` domain name: `http://<hostname>.local:<port>/sse`. Print a prominent security warning regarding the lack of authentication.

## Consequences
### Positive
- **Default Security**: Users running the server locally are protected by default from network-wide access.
- **Convenient Sharing**: Team members on the same network can access the server using a stable `.local` address without needing to configure static IPs or dynamic DNS.
- **Explicit Consent**: Users are forced to make a conscious choice about exposing their environment during the onboarding process.

### Negative / Risks
- Teams operating in environments where mDNS (.local resolution) is disabled by corporate firewalls/policies will still need to manually configure IPs or use Tailscale/VPNs.

## References
- Issue: #N / PR: #N
