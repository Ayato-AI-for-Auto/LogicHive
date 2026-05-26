# ADR-007: Continuous Pre-release Build Pipeline for Develop Branch

- **Date**: 2026-05-26
- **Status**: Accepted
- **Deciders**: ayato-labs (Human), Antigravity (Agent)

## Context
LogicHive relies on Windows native executables (`.exe`) to provide container-free local environments. To test new features in production-like local environments during development, we need to continuously build and test the `.exe` file whenever the `develop` branch is updated. Relying solely on `semantic-release`'s default publish outputs blocks continuous builds on the `develop` branch if semantic commits are not parsed or if version numbers do not increment.

## Decision
We decided to update the CI/CD pipeline to continuously build and deploy pre-release executables:
1. **Always Build on Develop**: Bypass the `new_release_published == 'true'` condition for the `build_exe` job when the push occurs on the `develop` branch.
2. **Rolling Tag ("v-develop")**: Upload the development executable (`LogicHive-MCP-dev.exe`) to a persistent, rolling pre-release tag `v-develop` on GitHub Releases.
3. **Automatic Release Creation**: Use `gh release create --prerelease` to automatically bootstrap the `v-develop` tag if it does not yet exist.

## Consequences
### Positive
- **Instant Local Verification**: Developers can download the latest `.exe` from the `v-develop` pre-release at any time for live testing.
- **Unblocked Integration**: Development pipeline does not stall when semantic-release determines that no new official version should be cut.

### Negative / Risks
- **Asset Overwrite**: The `v-develop` tag is rolling (using `--clobber`), meaning previous development builds are overwritten, which is acceptable since history is kept in Git.
