# ADR-003: Rejection of Docker-in-Docker for Internal Execution

## Status
Accepted

## Context
To verify logic assets, the system needs an isolated execution environment. Initially, spawning Docker containers (Docker-in-Docker) was considered for polyglot support.

## Decision
We **explicitly rejected** using Docker internally (DinD or socket mounting) for test execution. We shifted to:
1. **Current**: process-level isolation using `uv venv`.
2. **Future**: WebAssembly (WASM) or MicroVMs (Firecracker).

## Consequences
- **Enterprise Security**: Eliminates the need for "Privileged Mode" or mounting the host Docker socket, which is typically banned by IT security audits.
- **Serverless Compatibility**: Allows LogicHive to run in serverless environments (Cloud Run, Fargate) where DinD is impossible.
- **Performance**: `uv` provides millisecond-level startup for Python environments, far outperforming Docker container overhead.
