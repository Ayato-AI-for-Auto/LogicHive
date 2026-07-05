# [0.30.0](https://github.com/ayato-labs/LogicHive/compare/v0.29.0...v0.30.0) (2026-07-05)


### Bug Fixes

* **core:** resolve linting and syntax issues in LLM raw output recording ([79b0989](https://github.com/ayato-labs/LogicHive/commit/79b0989ec263b73ec109a970a679cc40fe489332))


### Features

* **core:** record raw LLM outputs and provider metadata (ADR-0033) ([0ef5657](https://github.com/ayato-labs/LogicHive/commit/0ef56571759eebfa63c924b6b32224084fba0702))
* **scripts:** add database maintenance and diagnostic tools ([1ab2795](https://github.com/ayato-labs/LogicHive/commit/1ab27951215aa866f89f6f8856e40e9f1d10cfcb))

# [0.29.0](https://github.com/ayato-labs/LogicHive/compare/v0.28.0...v0.29.0) (2026-07-05)


### Features

* **core:** implement embedding resilience and recovery (ADR-0031) ([39cf806](https://github.com/ayato-labs/LogicHive/commit/39cf80657d2a6f1b9d5606ead42c4b2442646612))
* **eval:** soften AI Gate veto power and update scoring (ADR-0032) ([ac46e03](https://github.com/ayato-labs/LogicHive/commit/ac46e038d6a6ff237a88598796a05b36307ca3b7))

# [0.28.0](https://github.com/ayato-labs/LogicHive/compare/v0.27.1...v0.28.0) (2026-07-05)


### Features

* update .gitignore to exclude storage data and backup files ([f490338](https://github.com/ayato-labs/LogicHive/commit/f4903384efa873d4161c91b551eee0fe3dcd6cae))

## [0.27.1](https://github.com/ayato-labs/LogicHive/compare/v0.27.0...v0.27.1) (2026-07-04)


### Bug Fixes

* **sandbox:** pass result_file and add memory monitoring to fallback execute ([b28e1e1](https://github.com/ayato-labs/LogicHive/commit/b28e1e1b02252ade684392636d6c79a9f3b649fe))

# [0.27.0](https://github.com/ayato-labs/LogicHive/compare/v0.26.0...v0.27.0) (2026-07-04)


### Bug Fixes

* **core:** improve plugin directory discovery for PyInstaller bundles ([d1ff76f](https://github.com/ayato-labs/LogicHive/commit/d1ff76fe0843611bbec1b65ced15bf803b121063))
* remove stale (1) duplicate files causing test failures ([aaf5d78](https://github.com/ayato-labs/LogicHive/commit/aaf5d7874cc10f5539e6f374878bde66c9a36d2e))


### Features

* **core:** implement disk space checks and improve pool cleanup logic ([b74219b](https://github.com/ayato-labs/LogicHive/commit/b74219bfd8f9f98f55bfcfc9a2d1c7f3c03a4fc2))
* ignore logichive.db.bak in .gitignore ([100f55e](https://github.com/ayato-labs/LogicHive/commit/100f55e98420feacd8ff6c09e56f8cc7d65142b3))

# [0.26.0](https://github.com/ayato-labs/LogicHive/compare/v0.25.0...v0.26.0) (2026-06-18)


### Features

* add developer-focused batch files for setup, config, and execution ([fafdd06](https://github.com/ayato-labs/LogicHive/commit/fafdd0633cf00caae0397115e68a5af5e190be42))

# [0.25.0](https://github.com/ayato-labs/LogicHive/compare/v0.24.0...v0.25.0) (2026-06-17)


### Features

* add PyInstaller spec for dual-binary packaging and diagnostic script for ChromaDB telemetry ([69f076b](https://github.com/ayato-labs/LogicHive/commit/69f076bddb574bc1e752f5a4c36bfe31dc785ca2))

# [0.24.0](https://github.com/ayato-labs/LogicHive/compare/v0.23.0...v0.24.0) (2026-06-17)


### Features

* add PyInstaller spec file for LogicHive hub and settings binaries ([5a239a1](https://github.com/ayato-labs/LogicHive/commit/5a239a1ca4834859937b8595bbf13d050538773b))

# [0.23.0](https://github.com/ayato-labs/LogicHive/compare/v0.22.0...v0.23.0) (2026-06-16)


### Features

* add GitHub Actions workflow for building Windows executables with Nuitka ([a250154](https://github.com/ayato-labs/LogicHive/commit/a250154ba6084a6b8ef0cc16dcf75441a9ab1b8c))
* add GitHub Actions workflow to build and release Windows executables using Nuitka ([9b14cfd](https://github.com/ayato-labs/LogicHive/commit/9b14cfd5c5fee5c4972500dd0679ff4888a55b2b))
* add GitHub Actions workflow to build Windows executables using Nuitka ([0fed1d6](https://github.com/ayato-labs/LogicHive/commit/0fed1d6387b51f5ddd004e58949b20c51abd6549))
* add GitHub Actions workflow to build Windows executables using Nuitka ([ff93bbb](https://github.com/ayato-labs/LogicHive/commit/ff93bbb0a5bef9eb1e7ad397104442101d00874d))
* add GitHub Actions workflow to build Windows executables using Nuitka ([09f4e69](https://github.com/ayato-labs/LogicHive/commit/09f4e694ddc5f1e43c8e42c08a2874d975c45d7e))
* add GitHub Actions workflow to build Windows executables using Nuitka ([e02701c](https://github.com/ayato-labs/LogicHive/commit/e02701c4b19e85553ba70bde60ccb9f2280a931b))
* add GitHub Actions workflow to build Windows executables using Nuitka ([c4fa932](https://github.com/ayato-labs/LogicHive/commit/c4fa932be26a0749cc1e125b2463d75b1f5b6d90))
* add GitHub Actions workflow to build Windows executables using Nuitka ([5e54cb2](https://github.com/ayato-labs/LogicHive/commit/5e54cb2a63546973859eb07d03d9a5f03da3140a))
* add GitHub Actions workflow to build Windows executables using Nuitka ([f3f274d](https://github.com/ayato-labs/LogicHive/commit/f3f274d82431286a5d1274816c5f34efb2510b36))
* add GitHub Actions workflow to build Windows executables using Nuitka ([b1f4ca8](https://github.com/ayato-labs/LogicHive/commit/b1f4ca87c2b27b9ad18a1d02481774cfee6c349a))
* add GitHub Actions workflow to build Windows executables using Nuitka ([06f37fd](https://github.com/ayato-labs/LogicHive/commit/06f37fd88f4dcf08906c114c83129ba4f33155e7))
* add windows setup and launch batch scripts ([3d35251](https://github.com/ayato-labs/LogicHive/commit/3d352518040eb362937a6f9740deb38652f2f327))
* implement asynchronous orchestrator for function lifecycle management and add vector store integration ([ca42706](https://github.com/ayato-labs/LogicHive/commit/ca427062e411bd86181aca7c1ac30ee63a0b0630))
* implement centralized structured logging system using loguru with JSON output and automatic rotation ([b9b8192](https://github.com/ayato-labs/LogicHive/commit/b9b8192845a09f9b33c6f535518c44cbb68279f8))
* implement multi-engine distribution CI/CD pipeline with PyInstaller and Nuitka build support ([be9a480](https://github.com/ayato-labs/LogicHive/commit/be9a480b9b9c65a57350fc28d0c650a9e1384392))
* implement Nuitka build workflow and PyInstaller configuration for Windows distribution ([8a544ed](https://github.com/ayato-labs/LogicHive/commit/8a544ed156bd2e961b88742b4e847894ed1819a2))

# [0.22.0](https://github.com/ayato-labs/LogicHive/compare/v0.21.0...v0.22.0) (2026-06-17)


### Features

* implement asynchronous orchestrator for function lifecycle management and add vector store integration ([ca42706](https://github.com/ayato-labs/LogicHive/commit/ca427062e411bd86181aca7c1ac30ee63a0b0630))
* implement centralized structured logging system using loguru with JSON output and automatic rotation ([b9b8192](https://github.com/ayato-labs/LogicHive/commit/b9b8192845a09f9b33c6f535518c44cbb68279f8))
* implement Nuitka build workflow and PyInstaller configuration for Windows distribution ([8a544ed](https://github.com/ayato-labs/LogicHive/commit/8a544ed156bd2e961b88742b4e847894ed1819a2))
* implement EvaluationManager with dynamic plugin discovery and PyInstaller path support ([4290b5d](https://github.com/ayato-labs/LogicHive/commit/4290b5dfb1088a617d14aad31dbf4a480c31cbaf))
* add GitHub Actions workflow to build and release Windows executables using Nuitka ([9b14cfd](https://github.com/ayato-labs/LogicHive/commit/9b14cfd5c5fee5c4972500dd0679ff4888a55b2b))
* implement multi-engine distribution CI/CD pipeline with PyInstaller and Nuitka build support ([be9a480](https://github.com/ayato-labs/LogicHive/commit/be9a480b9b9c65a57350fc28d0c650a9e1384392))
* add GitHub Actions workflow to build Windows executables using Nuitka ([0fed1d6](https://github.com/ayato-labs/LogicHive/commit/0fed1d6387b51f5ddd004e58949b20c51abd6549))
* add Windows setup and launch batch scripts ([3d35251](https://github.com/ayato-labs/LogicHive/commit/3d352518040eb362937a6f9740deb38652f2f327))

# [0.22.0-dev.1](https://github.com/ayato-labs/LogicHive/compare/v0.21.0...v0.22.0-dev.1) (2026-06-13)


### Features

* implement EvaluationManager with dynamic plugin discovery and PyInstaller path support ([4290b5d](https://github.com/ayato-labs/LogicHive/commit/4290b5dfb1088a617d14aad31dbf4a480c31cbaf))

# [0.21.0-dev.2](https://github.com/ayato-labs/LogicHive/compare/v0.21.0-dev.1...v0.21.0-dev.2) (2026-06-13)


## Features

* implement EvaluationManager with dynamic plugin discovery and PyInstaller path support ([4290b5d](https://github.com/ayato-labs/LogicHive/commit/4290b5dfb1088a617d14aad31dbf4a480c31cbaf))

# [0.21.0](https://github.com/ayato-labs/LogicHive/compare/v0.20.0...v0.21.0) (2026-06-13)


## Bug Fixes

* resolve mypy errors in EvaluationManager by refining type annotations ([6491ef2](https://github.com/ayato-labs/LogicHive/commit/6491ef25734341d6c2ce609e9408cd55c211dc2d))


## Features

* implement dynamic plugin discovery for EvaluationManager and increment package version ([37558c4](https://github.com/ayato-labs/LogicHive/commit/37558c4b249a2a254629c1eecd75dee19bd3feb1))
* implement interactive network recovery for port conflicts and simplify dev_run.bat execution flow ([504bead](https://github.com/ayato-labs/LogicHive/commit/504bead4419f835e83ea484bb899606276747399))

# [0.21.0-dev.1](https://github.com/ayato-labs/LogicHive/compare/v0.20.0...v0.21.0-dev.1) (2026-06-13)


### Bug Fixes

* resolve mypy errors in EvaluationManager by refining type annotations ([6491ef2](https://github.com/ayato-labs/LogicHive/commit/6491ef25734341d6c2ce609e9408cd55c211dc2d))


### Features

* implement dynamic plugin discovery for EvaluationManager and increment package version ([37558c4](https://github.com/ayato-labs/LogicHive/commit/37558c4b249a2a254629c1eecd75dee19bd3feb1))
* implement interactive network recovery for port conflicts and simplify dev_run.bat execution flow ([504bead](https://github.com/ayato-labs/LogicHive/commit/504bead4419f835e83ea484bb899606276747399))

# [0.20.0-dev.3](https://github.com/ayato-labs/LogicHive/compare/v0.20.0-dev.2...v0.20.0-dev.3) (2026-06-13)


### Features

* implement interactive network recovery for port conflicts and simplify dev_run.bat execution flow ([504bead](https://github.com/ayato-labs/LogicHive/commit/504bead4419f835e83ea484bb899606276747399))

# [0.20.0-dev.2](https://github.com/ayato-labs/LogicHive/compare/v0.20.0-dev.1...v0.20.0-dev.2) (2026-06-13)


### Bug Fixes

* resolve mypy errors in EvaluationManager by refining type annotations ([6491ef2](https://github.com/ayato-labs/LogicHive/commit/6491ef25734341d6c2ce609e9408cd55c211dc2d))


### Features

* implement dynamic plugin discovery for EvaluationManager and increment package version ([37558c4](https://github.com/ayato-labs/LogicHive/commit/37558c4b249a2a254629c1eecd75dee19bd3feb1))

# [0.20.0-dev.1](https://github.com/ayato-labs/LogicHive/compare/v0.19.0...v0.20.0-dev.1) (2026-06-13)


### Bug Fixes

* resolve Ruff F401 by explicitly declaring re-exports in __all__ ([2117104](https://github.com/ayato-labs/LogicHive/commit/211710481262bed898a6692cb2b319f9157ff4a7))
* restore network utility functions to mcp_server.py to satisfy tests ([447cfcf](https://github.com/ayato-labs/LogicHive/commit/447cfcf7db46cfcb58c57f271f38a8af52ed976f))


### Features

* add MCP server background vulnerability scanner and unit tests for scoring pipeline ([31e2135](https://github.com/ayato-labs/LogicHive/commit/31e2135f53f0a52b15ff5d48bea1ea6088c1a1b2))
* implement automated network port recovery and add GitHub Actions CI/CD pipeline for Windows build and release ([4bbd474](https://github.com/ayato-labs/LogicHive/commit/4bbd4743b0eedec9e40cc50b30a6f656886216dd))
* implement periodic vulnerability scanning and add defensive type checking to prevent NoneType errors ([581371a](https://github.com/ayato-labs/LogicHive/commit/581371a3a2de6b6cb8d09653ac46358c3263534e))
* implement periodic vulnerability scanning and automated security auditing for stored functions. ([ee55cf7](https://github.com/ayato-labs/LogicHive/commit/ee55cf76a0e492bcb25dc9618c98eb8f58790cf9))
