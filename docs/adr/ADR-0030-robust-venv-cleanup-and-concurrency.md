# ADR-0030: Robust Virtual Environment Cleanup and Concurrency Control

- **Date**: 2026-06-29
- **Status**: Accepted
- **Deciders**: Antigravity, ayato-labs

## Context

LogicHive uses a pre-warmed virtual environment (venv) pooling system to reduce cold-start latency when running user-defined logic. However, several storage leakage symptoms were identified:
1. **Accumulation under home directory and workspace**: High-disk-space virtual environments (often containing large packages like `torch` and `numpy`) accumulated continuously.
2. **Duplicate creation**: The background replenishment worker only evaluated the pool queue size (`queue.qsize()`). Because environment setup involves running `uv pip install` which takes significant time, multiple duplicate creation tasks were triggered in subsequent worker cycles before the initial environment was queued.
3. **Windows file locks**: When an environment was released, `shutil.rmtree` was called immediately. If file handles from recently terminated Python processes or system scanners were still open, deletion failed with `PermissionError` (Access is denied), causing the folder to be abandoned.
4. **Orphaned cleanup directories**: Directories renamed to `pools_cleanup_*` during startup or shutdown were left behind if deletion failed, with no subsequent sweep mechanism to purge them.

## Decision

We will implement a robust virtual environment lifecycle manager that enforces concurrency control, resilient deletions, and periodic garbage collection of orphaned files.

### 1. Concurrency Control (In-Progress Tracking)
Introduce an `in_progress` counter (`self._in_progress_replenishments`) for each environment specification. The worker will evaluate `needed = POOL_MAX_SIZE - (current_size + in_progress)` before spawning new creation tasks.

### 2. Resilient Deletion with Delayed Retries
When an environment is released:
- Attempt deletion with a retry loop (4 attempts with escalating delays: 0.1s, 0.5s, 1.0s, 2.0s).
- If deletion fails, attempt to rename the environment to a parent folder path.
- If both fail, spawn a delayed background task to execute the cleanup again after a 5.0-second delay, allowing the OS to fully release any residual file handles.

### 3. Periodic and Startup Garbage Collection
- During manager initialization, scan the parent directory and delete any matching `pools_cleanup_*` folders.
- In the background worker loop, periodically sweep and remove orphaned `pools_cleanup_*` directories.

## Consequences

### Positive
- **Zero Disk Leakage**: Environments are guaranteed to be cleaned up, preventing storage exhaustion.
- **Efficient Resource Usage**: No duplicate virtual environments are created, reducing CPU and network usage during replenishment.
- **Windows Resiliency**: Handles file locking limits gracefully without crashing or leaking memory.

### Negative / Risks
- **Background Tasks**: Spawns short-lived background tasks for retries, which must be safely managed during shutdown (handled via CancelledError guards).

## References
- Issue: Virtual environment storage leak
- ADR-0015 (Lightweight ephemeral environments)
