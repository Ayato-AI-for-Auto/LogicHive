# ADR-0029: Multi-Engine Distribution Strategy

- **Date**: 2026-06-14
- **Status**: Proposed
- **Deciders**: Gemini CLI, ayato-labs

## Context
LogicHive is currently distributed as Windows executables. We are testing Nuitka as an alternative to PyInstaller to provide better performance and better anti-reverse engineering protection. However, Nuitka builds can be experimental or have different compatibility profiles. We need a way to distribute both versions without causing naming conflicts in GitHub Releases or confusing the users.

Previously, Nuitka builds were only available as GitHub Action Artifacts, while PyInstaller builds were uploaded to GitHub Releases.

## Decision
We will adopt a "Multi-Engine Distribution Strategy" where both PyInstaller (Standard) and Nuitka (Optimized) binaries are uploaded to the same GitHub Release.

### Naming Convention
To avoid conflicts and provide clarity:
- **Standard (PyInstaller)**: `LogicHive-Hub.exe`, `LogicHive-Settings.exe`
- **Optimized (Nuitka)**: `LogicHive-Hub-nuitka.exe`, `LogicHive-Settings-nuitka.exe`
- **Development Builds**: Append `-dev` before the engine suffix if applicable, or as `LogicHive-Hub-dev-nuitka.exe`.

### CI/CD Integration
- Both `ci_cd_main.yml` and `nuitka_build.yml` will target the same release tags (`v-develop` for rolling builds, and semantic version tags for releases).
- Explicit `gh release upload --clobber` will be used, with a proactive deletion step for development releases to ensure reliability.

## Consequences
### Positive
- **User Choice**: Users can choose between the standard stable build and the optimized version.
- **Improved Troubleshooting**: Clear distinction between build engines helps isolate environment-specific bugs.
- **Collision Prevention**: Different filenames prevent `HTTP 422: Validation Failed` errors during concurrent or sequential uploads to the same release.

### Negative / Risks
- **Release Bloat**: Doubling the number of assets per release.
- **User Confusion**: Non-technical users might not know which one to pick (mitigated by documentation).

## References
- Issue: #14 (Nuitka build fix)
- ADR-0011 (Dual binary separation)
- ADR-0028 (Resource path resolution)
