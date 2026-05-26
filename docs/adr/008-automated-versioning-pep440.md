# ADR-008: Automated Versioning with Semantic Release and PEP 440 Compliance

- **Date**: 2026-05-27
- **Status**: Accepted
- **Deciders**: Gemini CLI (Agent), ayato-labs (User)

## Context
Manually managing version numbers across multiple files (`pyproject.toml`, `src/core/__init__.py`) is error-prone and inconsistent. Furthermore, Python packaging tools like `uv` strictly enforce [PEP 440](https://peps.python.org/pep-0440/) versioning standards. Traditional SemVer pre-release tags (e.g., `0.10.0-develop.1`) cause build failures in the Python ecosystem. We need a system that automates version increments, synchronizes them across the codebase, and adheres to Python's specific versioning requirements.

## Decision
We will use `semantic-release` to automate the versioning process, integrated with a custom synchronization script.

Key components of the implementation:
1.  **Semantic Release Integration**: Use `semantic-release` in the CI/CD pipeline (GitHub Actions) to determine the next version based on commit messages (Conventional Commits).
2.  **PEP 440 Compliance**: Configure `semantic-release` to use `.devN` instead of `-develop.N` for pre-releases on the `develop` branch (e.g., `0.10.0.dev1`) to maintain compatibility with `uv` and `pip`.
3.  **Codebase Synchronization**: Utilize `tools/migration/update_version.py` as a `prepare` hook in `semantic-release` to update `pyproject.toml` and `src/core/__init__.py` automatically.
4.  **Runtime Consistency**: Ensure the application logs and metadata use the version string provided by `src/core/__init__.py`, which is now guaranteed to match the release tag.

## Consequences
### Positive
- **Single Source of Truth**: Versions are managed in one place and propagated automatically.
- **Tooling Compatibility**: Strict adherence to PEP 440 ensures `uv sync` and other build tools work without manual intervention.
- **Traceability**: Application logs directly reflect the release version, simplifying troubleshooting for remote users.
- **Automation**: Eliminates "forgetting to bump version" before a release.

### Negative / Risks
- **Commit Format Dependency**: Requires team-wide adherence to Conventional Commits for correct version calculation.
- **CI Dependency**: Versions are only bumped during CI runs, which might lead to "dirty" versions during local development (though this is mitigated by `.dev` tagging).

## References
- Issue: N/A
- PR: N/A
- PEP 440: https://peps.python.org/pep-0440/
- tool: semantic-release
