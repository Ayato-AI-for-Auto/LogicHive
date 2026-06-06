# ADR-0019: Windows Unified CI Test Environment

- **Date**: 2026-06-07
- **Status**: Accepted
- **Deciders**: ayato-labs (Human Developer), Antigravity (AI Agent)

## Context
LogicHive is a cross-platform backend system but contains critical OS-level integration features specifically targeting the Windows platform, such as the UAC admin execution check, scheduled tasks setup, and uninstaller bindings (`src/core/system/windows_tasks.py`).

Previously, the main `test` job in GitHub Actions ran on a Linux runner (`ubuntu-latest`). Under this configuration, Windows-native APIs like `ctypes.windll` were unavailable, which forced us to skip Windows-specific test suites in CI. This created a gap in CI test coverage, leaving OS integration logic unverified on push/pull requests.

## Decision
We decided to unify the test runner environment to Windows (`windows-latest`) in GitHub Actions:
- Change the `test` job's `runs-on` property from `ubuntu-latest` to `windows-latest` in `.github/workflows/ci_cd_main.yml`.
- Keep the `@pytest.mark.skipif(sys.platform != "win32", ...)` decorators on Windows-only tests so that local non-Windows development environments (macOS, Linux) can still run the generic test suite and bypass OS-specific checks gracefully.

### Trade-off Comparison
| Metric / Aspect | Option A: Linux Runner (`ubuntu-latest`) | Option B: Windows Runner (`windows-latest`) [Selected] |
| :--- | :--- | :--- |
| **Billing Multiplier** | 1.0x (Standard billing) | 2.0x (Double billing minutes) |
| **CI Execution Time** | ~1 min | ~1 min 15s |
| **OS Native API Test** | Impossible (Tests must be skipped) | Fully Supported (All task integrations verified) |
| **Windows Task Coverage** | 0% on CI | 100% on CI |

## Consequences
### Positive
- **CI Integrity**: All Windows scheduled tasks registration and admin privileges logic are validated automatically in CI on every push and PR.
- **Unified Environment**: Both tests and executable packaging (`build_exe` job) now run in Windows-aligned environments.

### Negative / Risks
- **Resource Consumption**: Slightly increased GitHub Actions minutes usage (2x billing rate).
- **Boot Latency**: Windows virtual machines take slightly longer to boot up on GitHub Actions compared to lightweight Linux containers.

## References
- Workflow file: [.github/workflows/ci_cd_main.yml](file:///c:/Users/saiha/My_Service/programing/MCP/LogicHive/.github/workflows/ci_cd_main.yml)
- Test file: [test_windows_tasks.py](file:///c:/Users/saiha/My_Service/programing/MCP/LogicHive/tests/system/test_windows_tasks.py)
