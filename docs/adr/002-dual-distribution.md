# ADR-002: Dual Distribution Strategy (OCI Container & Windows EXE)

## Status
Accepted

## Context
Commercializing LogicHive in enterprise environments faces friction from Docker Desktop licensing (paid for large businesses) and the technical complexity of container runtimes on Windows.

## Decision
We adopted a **Dual Distribution Strategy**:
1. **OCI Container Image**: For cloud-native and Linux-heavy environments.
2. **Windows Standalone EXE**: For zero-friction use in corporate Windows environments.

## Consequences
- **Zero Friction**: Enterprise users can run LogicHive by double-clicking a `.exe` without worrying about Docker licenses.
- **Platform Agnostic**: SSE allows a Windows `.exe` to serve Mac/Linux clients, effectively eliminating "Windows-only" constraints.
- **Automated Delivery**: GitHub Actions now builds both Docker images and Windows binaries upon every release.
