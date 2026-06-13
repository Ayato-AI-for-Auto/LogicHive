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
