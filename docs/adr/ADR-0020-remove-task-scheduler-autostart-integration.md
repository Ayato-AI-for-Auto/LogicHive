# ADR-0020: Remove Task Scheduler Auto-Start Integration

- **Date**: 2026-06-07
- **Status**: Accepted
- **Deciders**: ayato-labs (User), Gemini (Agent)

## Context
LogicHive originally implemented an auto-start integration with the Windows Task Scheduler, including UAC elevation requests (`IsUserAnAdmin`/`ShellExecuteW`) and scheduled tasks configuration (`schtasks`). During review of the MVP scope, this feature was determined to add unnecessary complexity, security/privilege warnings, and maintenance overhead without providing core value to the LogicHive vault functionality.

## Decision
We decided to completely remove the Task Scheduler integration, including:
1. Deleting `windows_tasks.py` and its corresponding test file `test_windows_tasks.py`.
2. Removing the auto-start task configuration UI cards and UAC privilege checks from the Settings UI.
3. Keeping the uninstaller wizard intact as a manual action.

## Consequences
### Positive
- Reduced security surface area (no longer requesting UAC/administrator elevation during setup).
- Simplified codebase and cleaner Settings UI.
- Reduced testing scope (no longer mocking `schtasks` or `ctypes.windll` or skipping Windows-only tasks in CI).

### Negative / Risks
- Users must manually start LogicHive or configure their own startup options (e.g., using the Windows Startup Folder).

## References
- ADR-0019: Unified CI runner environment to Windows.
