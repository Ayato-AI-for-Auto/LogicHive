# ADR-0025: Windows Native Sandbox and Multi-Language Architecture

- **Date**: 2026-06-07
- **Status**: Proposed
- **Deciders**: ayato-labs (User), Antigravity (Agent)

## Context
LogicHive executes user-provided code and test code to verify correctness before storing it.
Currently, this execution relies on `asyncio.create_subprocess_exec` running the local python interpreter directly without OS-level sandboxing, other than a basic socket hook inside the python test harness.
This setup has two main limitations:
1. **Security & Resource Limits**: Memory limits are monitored via an asynchronous polling task (`psutil`), which can be bypassed if memory spikes rapidly between poll intervals. Process spawning (fork-bombs) is not restricted.
2. **Language Isolation**: The current execution logic is coupled with Python's runtime lifecycle, making it difficult to execute scripts or binaries written in other languages (such as Node.js, C/C++, Go, or Rust).

We need a secure, lightweight, Docker-free sandbox mechanism that works out-of-the-box on Windows client machines, doesn't require administrator (UAC) privileges, and allows executing arbitrary commands or binaries securely.

## Decision
We will decouple sandbox orchestration from language-specific executors by introducing a unified `BaseSandbox` interface, and implement a Windows-native sandbox using Windows Job Objects via `ctypes`.

### 1. Sandbox Abstraction
We define a `BaseSandbox` interface:
```python
class BaseSandbox(ABC):
    @abstractmethod
    async def execute_command(
        self,
        cmd: list[str],
        cwd: str,
        env: dict[str, str] | None = None,
        timeout: float = 10.0,
        memory_limit_mb: int = 256,
    ) -> ExecutionResult:
        pass
```

### 2. Windows Native Sandbox (`WindowsNativeSandbox`)
Using Windows native API calls via Python `ctypes`, we will:
- **Create a Job Object**: Call `CreateJobObjectW` to establish a boundary.
- **Configure Limits**:
  - **Memory Limit**: Configure `JobObjectExtendedLimitInformation` with `ProcessMemoryLimit` and `JobMemoryLimit` to cap memory at the OS level (avoiding poll-based bypasses).
  - **Process Count Limit**: Limit `ActiveProcessLimit` to 5-10 processes to prevent fork bombs.
  - **CPU Limit**: Configure CPU rate limits or limits on execution time.
- **Associate Process with Job**: Launch the subprocess using the Windows-specific flag `CREATE_SUSPENDED` (value `0x00000004`), associate the new process handle with the Job Object using `AssignProcessToJobObject`, and then resume the main thread.
- **Network Restriction**: Keep harness-level socket blocks, and optionally run with reduced privilege tokens or Windows-specific firewall rules.

This guarantees process-level resource constraints natively on Windows without Docker daemon or hypervisor overhead.

## Consequences
### Positive
- **Guaranteed Isolation**: Memory and process spawning limits are enforced directly by the Windows kernel, completely preventing out-of-memory crashes on the host system or system lockups from fork-bombs.
- **Language Agnostic**: Any executor (Python, JavaScript, C++) can write its code/test harness files to a temporary directory, and then pass the execution command to the `WindowsNativeSandbox`.
- **Zero Overhead**: No VM or container startup latency.
- **No Admin Required**: Job Objects and suspended process execution do not require Administrator/UAC elevation.

### Negative / Risks
- **Windows Only**: Windows APIs are platform-dependent. However, for a Windows-first client app (`.exe`), this is acceptable. We will implement a clean fallback or abstract runner for other platforms (e.g. Linux Bubblewrap / default subprocess runner).

## References
- Issue: #N / PR: #N
