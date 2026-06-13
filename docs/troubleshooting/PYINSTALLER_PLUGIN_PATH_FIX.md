# Troubleshooting: PyInstaller Plugin Directory Discovery Failure

- **Date**: 2026-06-14
- **Status**: Resolved
- **Issue**: `EvaluationManager: Plugins directory not found` in frozen binaries.

## Symptoms
When running LogicHive as a bundled executable (e.g., `LogicHive-Hub.exe`), the following error appears in the logs:
`ERROR | core.evaluation.manager - EvaluationManager: Plugins directory not found at C:\Users\...\AppData\Local\Temp\_MEIXXXX\src\core\evaluation\plugins`

This prevents the quality gates (Security, Runtime, Static analysis) from loading any evaluators, resulting in a default low score or system errors during verification.

## Root Cause Analysis
The issue was a mismatch between the **PyInstaller build configuration** and the **application's path resolution logic**.

1. **Build Config (`LogicHive.spec`)**:
   The spec file bundles the source directory into a sub-folder named `engine/src`:
   ```python
   common_datas += [(os.path.join(project_root, 'src'), 'engine/src')]
   ```

2. **Application Logic (`src/core/evaluation/manager.py`)**:
   The `EvaluationManager` was checking for the plugins in:
   - `_MEIPASS/core/evaluation/plugins`
   - `_MEIPASS/src/core/evaluation/plugins`
   
   It did **not** account for the `engine/src/` prefix created by the spec file mapping.

## Resolution
Updated `src/core/evaluation/manager.py` to include the `engine/src` path as a fallback when running in a frozen environment.

```python
if not plugins_dir.exists():
    # LogicHive.spec copies 'src' to 'engine/src'
    plugins_dir = base_dir / "engine" / "src" / "core" / "evaluation" / "plugins"
```

## Verification Results
- **Unit Tests**: Passed (Source mode path resolution still works).
- **Integration Tests**: Passed.
- **Manual Verification**: Confirmed path alignment with `LogicHive.spec` structure.

## Related
- ADR-0028: Resource Path Resolution for Frozen Binaries
- File: `src/core/evaluation/manager.py`
