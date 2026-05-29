# ADR-0012: Centralized User Data Storage

- **Date**: 2026-05-29
- **Status**: Proposed
- **Deciders**: Gemini CLI, ayato-labs

## Context
Initially, LogicHive stored logs, databases, and temporary execution environments within the application's installation directory (e.g., in a `storage/` folder relative to the executable). 

While this "portable" approach works for simple tools, it faces several critical issues in a professional Windows environment:
1. **Permission Denied Errors**: When installed in `C:\Program Files\`, the application cannot write to its own directory without administrative privileges.
2. **Data Fragmentation**: Re-installing or updating the application might lead to data loss or orphaned log files spread across different installation paths.
3. **Backup Difficulty**: Users have to hunt for logs and data in various locations.
4. **Platform Conventions**: Modern Windows/Unix developer tools (e.g., `.git`, `.docker`, `.npm`) use a hidden "dot directory" in the user's home to centralize state.

## Decision
Consolidate all mutable application state into a single centralized directory in the user's home folder: `C:\Users\<User>\.logichive` (aliased as `~/.logichive`).

The folder structure will be:
- `~/.logichive/`
  - `.env` (Central configuration)
  - `logs/` (Rotation-based JSONL and error logs)
  - `data/` (SQLite database, FAISS indices, mapping files)
  - `pools/` (Pre-warmed virtual environments for asset execution)

### Key Changes:
- **`src/core/logging_config.py`**: Update `log_dir` to `~/.logichive/logs`.
- **`src/core/config.py`**: 
    - Redefine `DATA_DIR` to `~/.logichive/data`.
    - Redefine `POOL_BASE_DIR` to `~/.logichive/pools`.
    - Ensure all paths (SQLite, FAISS) derive from these centralized roots.

## Consequences
### Positive
- **Windows Compliance**: Works perfectly without admin rights, even when installed in `Program Files`.
- **High Portability**: Users can migrate all LogicHive state by simply copying one folder.
- **Clean Installation**: The application directory remains read-only and clutter-free.
- **Standardization**: Follows the established pattern of major developer tools.

### Negative / Risks
- **Hidden Directory**: Users who don't show hidden files might find it harder to find the logs initially (mitigated by documentation).
- **Disk Usage**: Centralizing environments in the home directory might consume space on the OS drive (C:).

## References
- Issue: Centralizing application data
- Expert Panel Review: 5/5 experts recommended this transition.
