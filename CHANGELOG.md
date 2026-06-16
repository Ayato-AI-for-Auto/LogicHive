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
