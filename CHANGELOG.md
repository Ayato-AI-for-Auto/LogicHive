# [0.20.0](https://github.com/ayato-labs/LogicHive/compare/v0.19.0...v0.20.0) (2026-06-13)


### Bug Fixes

* resolve Ruff F401 by explicitly declaring re-exports in __all__ ([2117104](https://github.com/ayato-labs/LogicHive/commit/211710481262bed898a6692cb2b319f9157ff4a7))
* restore network utility functions to mcp_server.py to satisfy tests ([447cfcf](https://github.com/ayato-labs/LogicHive/commit/447cfcf7db46cfcb58c57f271f38a8af52ed976f))


### Features

* add MCP server background vulnerability scanner and unit tests for scoring pipeline ([31e2135](https://github.com/ayato-labs/LogicHive/commit/31e2135f53f0a52b15ff5d48bea1ea6088c1a1b2))
* implement automated network port recovery and add GitHub Actions CI/CD pipeline for Windows build and release ([4bbd474](https://github.com/ayato-labs/LogicHive/commit/4bbd4743b0eedec9e40cc50b30a6f656886216dd))
* implement periodic vulnerability scanning and add defensive type checking to prevent NoneType errors ([581371a](https://github.com/ayato-labs/LogicHive/commit/581371a3a2de6b6cb8d09653ac46358c3263534e))
* implement periodic vulnerability scanning and automated security auditing for stored functions. ([ee55cf7](https://github.com/ayato-labs/LogicHive/commit/ee55cf76a0e492bcb25dc9618c98eb8f58790cf9))

# [0.19.0](https://github.com/ayato-labs/LogicHive/compare/v0.18.0...v0.19.0) (2026-06-07)


### Features

* add multi-language execution fallback support, system E2E tests, and a dynamic plugin-based evaluation manager ([e0de13a](https://github.com/ayato-labs/LogicHive/commit/e0de13ae8db232283abbc32ba5b366943d39700b))
* implement DeterministicEvaluator for structural code analysis and add associated testing infrastructure ([75e0fa5](https://github.com/ayato-labs/LogicHive/commit/75e0fa570739bda7ac013f1c7e44521b343c1eb3))
* implement multi-language evaluation framework with language-specific executors and static analysis plugins ([5c5142f](https://github.com/ayato-labs/LogicHive/commit/5c5142ffe2ffb92df30a31c4af710bf562d97303))

# [0.18.0](https://github.com/ayato-labs/LogicHive/compare/v0.17.0...v0.18.0) (2026-06-07)


### Features

* implement periodic vulnerability scanning via OSV API with multiplicative RAG prioritization and supporting documentation ([c16afe5](https://github.com/ayato-labs/LogicHive/commit/c16afe5493a4f5abc6f922011faf5a56ee558f64))
* implement Windows-native sandbox using Job Objects for secure, multi-language process execution ([638307d](https://github.com/ayato-labs/LogicHive/commit/638307dca839d4ab609a3dc29e86f835002f29c1))

# [0.17.0](https://github.com/ayato-labs/LogicHive/compare/v0.16.0...v0.17.0) (2026-06-07)


### Features

* implement SQLite storage engine and add unit tests for scoring pipeline and system tests for RAG prioritization ([625ddf3](https://github.com/ayato-labs/LogicHive/commit/625ddf391b26aaca1c8b842a12a7524ce93b0680))
* implement SQLite storage engine and define ADR-021 for score-scaled multiplicative RAG prioritization ([253eaa8](https://github.com/ayato-labs/LogicHive/commit/253eaa83f71519aa188837a015375b7249628fc5))

# [0.16.0](https://github.com/ayato-labs/LogicHive/compare/v0.15.0...v0.16.0) (2026-06-06)


### Features

* add Flet-based settings and environment management UI to LogicHive ([b074890](https://github.com/ayato-labs/LogicHive/commit/b0748901f53509a8f4e15f1d714958cf57228cb3))

# [0.15.0](https://github.com/ayato-labs/LogicHive/compare/v0.14.0...v0.15.0) (2026-06-06)


### Features

* initialize MCP server and implement basic tools for function management and verification ([3d977ba](https://github.com/ayato-labs/LogicHive/commit/3d977bad721f8914c95fbb416d86ded8e9e7a825))

# [0.14.0](https://github.com/ayato-labs/LogicHive/compare/v0.13.0...v0.14.0) (2026-06-06)


### Features

* add system integration tests for Windows task management ([08bce84](https://github.com/ayato-labs/LogicHive/commit/08bce84f6c776ac4dca513dd625b134ad1dc1604))
* add Windows system tests and implement CI/CD pipeline for automated testing and release builds ([658dff2](https://github.com/ayato-labs/LogicHive/commit/658dff228e939365b6288cc157a71c66c0b2a7cc))
* implement automated CI/CD pipeline and add settings UI for system configuration ([77f513a](https://github.com/ayato-labs/LogicHive/commit/77f513a81dcbf7a6ef37c0bb18c3f9f806b354a7))
* implement bootstrapper to initialize core system services ([246c06c](https://github.com/ayato-labs/LogicHive/commit/246c06ce32f297ef50a8cc616b7dcd883970ea33))
* implement core MCP server infrastructure with dynamic configuration and modular project structure ([21daa6d](https://github.com/ayato-labs/LogicHive/commit/21daa6db1d9b3360b9cf423a3bce30e118f3964f))
* implement system bootstrapper and add PyInstaller build configuration for hub and settings binaries ([73aebbd](https://github.com/ayato-labs/LogicHive/commit/73aebbd7f416ce5ea08335821dae50bdb41d9213))
* implement thin settings client with dynamic virtual environment orchestration and system-wide OS integration ([6d332dd](https://github.com/ayato-labs/LogicHive/commit/6d332dd440dd2e1b4aa01d7d0d2063b66ad46731))

# [0.13.0](https://github.com/ayato-labs/LogicHive/compare/v0.12.0...v0.13.0) (2026-06-06)


### Features

* add sqlite debugging script and update environment configuration template to prioritize local-first models ([48f6267](https://github.com/ayato-labs/LogicHive/commit/48f6267ff1f55708473a2ddfd9124755bc5124ef))
* bump project version to 0.12.0 and add evaluation runner script for code hashing tests ([59e90b8](https://github.com/ayato-labs/LogicHive/commit/59e90b8126f928da7f07364e8f504c65bb450db0))
* implement automated entropy-based secret scanning tools for dogfooding and final audits ([659b57e](https://github.com/ayato-labs/LogicHive/commit/659b57e2ad442f3844387b95561b196bcca2e5a3))
* implement comprehensive testing suite and CI/CD pipeline for LogicHive ([a667801](https://github.com/ayato-labs/LogicHive/commit/a6678010955996f5e445cc6cb0dfbd5095f16cd8))
* implement concurrent file scanning with performance optimizations and expanded secret filtering ([40fa80c](https://github.com/ayato-labs/LogicHive/commit/40fa80c3bf28e11e2c1bb9e7973efbcc251e1abb))
* implement EphemeralPythonExecutor for secure, resource-monitored code execution with environment pooling support ([fdbe48e](https://github.com/ayato-labs/LogicHive/commit/fdbe48e683b59731ddf5ad7896055269a847f6f8))
* implement FastMCP server with search, retrieval, and validation tools alongside system integration tests ([5c03ab6](https://github.com/ayato-labs/LogicHive/commit/5c03ab67987b2f3bdf5f5879318defe049f284b7))
* implement Flet-based GUI for managing application configuration and system integrity checks ([dda1a60](https://github.com/ayato-labs/LogicHive/commit/dda1a60d6b7a4408e3eb9c03c4590d447003633b))
* implement MCP server with tool registration for searching, retrieving, saving, and debugging functions ([e5dad25](https://github.com/ayato-labs/LogicHive/commit/e5dad2552fb3ea0067dad751021818cbcc1a56f1))
* implement mcp_server with core function management tools and add system flow test suite ([7fbd20c](https://github.com/ayato-labs/LogicHive/commit/7fbd20cc2339c3316a369bb7af975cd4929c121f))
* implement PoolManager with background environment warming and non-blocking cleanup strategy ([4f1b4cc](https://github.com/ayato-labs/LogicHive/commit/4f1b4cc259bb63b21c16b2e666d9ef6cd89847dd))
* implement security scanner, add debug utilities, and update environment configuration. ([1378e3f](https://github.com/ayato-labs/LogicHive/commit/1378e3f616faee556c09a523e80af74b000c132c))
* implement SQLite database management and add system tests for configuration resolution and execution harness logic ([959b4a8](https://github.com/ayato-labs/LogicHive/commit/959b4a80646b0ff0d03f45d29dd879d63df3d6df))
* implement structured JSON logging and initialize MCP server infrastructure ([4845bfe](https://github.com/ayato-labs/LogicHive/commit/4845bfe804509ed5aa5fad3126615b5136cf091b))
* implement thread-safe SQLite database connector with loop-affinity handling and add comprehensive test infrastructure ([2efd2dc](https://github.com/ayato-labs/LogicHive/commit/2efd2dc00909ac691cf9e4ab50c2a1e8f659f96c))
* implement tiered .env configuration strategy and document hybrid deployment standard ([f6b02f6](https://github.com/ayato-labs/LogicHive/commit/f6b02f628ee156f7c623b6acb034a8d343b53329))
* implement tiered hybrid configuration strategy and standardize environment loading ([b11101e](https://github.com/ayato-labs/LogicHive/commit/b11101e44e84c14cd25fdb65c6e64c46986a57a0))
* introduce orchestrator module for async asset management and verification pipeline ([3469fd3](https://github.com/ayato-labs/LogicHive/commit/3469fd3a50fa361985d614b9f377b960be6960d0))

# [0.12.0](https://github.com/ayato-labs/LogicHive/compare/v0.11.0...v0.12.0) (2026-06-01)


### Features

* implement Flet-based settings UI for system configuration and diagnostics ([9025f38](https://github.com/ayato-labs/LogicHive/commit/9025f38bab5dc5e530342a0c32e1c508017a5277))

# [0.11.0](https://github.com/ayato-labs/LogicHive/compare/v0.10.0...v0.11.0) (2026-05-31)


### Features

* implement automated CI/CD pipeline with PyInstaller build and release support ([357bf1f](https://github.com/ayato-labs/LogicHive/commit/357bf1fcf50d50e9aabc852c293d20253aa8bba2))

# [0.10.0](https://github.com/ayato-labs/LogicHive/compare/v0.9.8...v0.10.0) (2026-05-31)


### Bug Fixes

* **build:** resolve PyInstaller metadata discovery failure and align binary names ([507951f](https://github.com/ayato-labs/LogicHive/commit/507951f1956757ed9da3ba3ef4e526d246f1d52e))
* **ci:** add write permissions to CLA check workflow ([d1ba8eb](https://github.com/ayato-labs/LogicHive/commit/d1ba8eb3f4c0db50623e30d529e532f2fd589058))
* **ci:** bypass astral-sh/setup-uv action due to download failures ([e874b60](https://github.com/ayato-labs/LogicHive/commit/e874b606fb9461c45be7d5001e47b31118f61c40))
* **ci:** ensure versioned pre-releases capture executables by fixing output logic ([ec1d8dd](https://github.com/ayato-labs/LogicHive/commit/ec1d8dda4fb71f4639f0ecdef84d7d919852bacc))
* **ci:** set LOGICHIVE_TESTING=true to skip API key validation during tests ([e08bd6a](https://github.com/ayato-labs/LogicHive/commit/e08bd6aac06b738a52946b6db87c827a4e7926b8))
* **config:** ensure LOGICHIVE_TESTING correctly bypasses GEMINI_API_KEY check ([c2c8de0](https://github.com/ayato-labs/LogicHive/commit/c2c8de004cbbdd7b48b5f9c8a265d0722577730e))
* correct development branch name from 'dev' to 'develop' ([57d2e85](https://github.com/ayato-labs/LogicHive/commit/57d2e857b92bbbc089a3ca654ddcc766600d608d))


### Features

* add centralized logging configuration and implement core MCP server infrastructure ([f270318](https://github.com/ayato-labs/LogicHive/commit/f270318fc6d08e8f5cc04b65bfc0c3bfdcfe3f96))
* add CI/CD pipeline for automated testing, semantic versioning, and Windows executable builds ([eccb10e](https://github.com/ayato-labs/LogicHive/commit/eccb10e37a9a8a2d55ab1f05cff9c448bddb7b90))
* add CI/CD pipeline for automated testing, semantic versioning, and Windows executable builds ([7d97c55](https://github.com/ayato-labs/LogicHive/commit/7d97c55a79b5f901407b969e6bc434f7c305a90c))
* add diagnostic scripts to test Flet port configuration and module imports ([f7ccf43](https://github.com/ayato-labs/LogicHive/commit/f7ccf430b2371d721644413e63b949a38bc95afb))
* add Flet-based GUI for system configuration and integrity diagnostics ([1dc8138](https://github.com/ayato-labs/LogicHive/commit/1dc81383b598d78bf7155ac8240f102ca38ba67e))
* add Flet-based settings UI and generate PyInstaller build specifications for hub and settings binaries. ([fdc0458](https://github.com/ayato-labs/LogicHive/commit/fdc045801e54acc100d568ee2d3fdd97dfaaa6d4))
* add PoolManager to pre-warm virtual environments and reduce cold start latency ([c0fd7f6](https://github.com/ayato-labs/LogicHive/commit/c0fd7f6955295e9981ae25931da82d31ee1fa8f4))
* add PyInstaller spec file for building LogicHive hub and settings binaries ([2a43909](https://github.com/ayato-labs/LogicHive/commit/2a43909d2e155fd977ddb7e1008c3730242e7480))
* add PyInstaller spec file to bundle hub and settings binaries ([db6adca](https://github.com/ayato-labs/LogicHive/commit/db6adca1c75f1efe94eb65f8140a1c51fd6c3cab))
* automate pre-releases for develop branch with specialized binary naming ([d063613](https://github.com/ayato-labs/LogicHive/commit/d06361314a3a1a7fc697c7f9ea35e48537f25db8))
* enable continuous pre-release builds for develop branch and update config loader for executable compatibility ([596e99f](https://github.com/ayato-labs/LogicHive/commit/596e99f3711bf26578d72849f8756fc1d1998d3c))
* implement asynchronous environment pool manager to eliminate cold start latency ([936fc56](https://github.com/ayato-labs/LogicHive/commit/936fc5625def407a73d8e9f09c51c3545054828c))
* implement centralized configuration management and structured logging system ([4cd0abe](https://github.com/ayato-labs/LogicHive/commit/4cd0abe24da4db4a4ca7546050c27bb394743782))
* implement comprehensive unit, chaos, and integration test suite with supporting configuration fixtures ([692bd5e](https://github.com/ayato-labs/LogicHive/commit/692bd5ed20b2f3d70f25c5ef61c2ae11ebc799b5))
* implement comprehensive unit, integration, and chaos test suites for code evaluation and system resilience ([5ab9697](https://github.com/ayato-labs/LogicHive/commit/5ab96978f73e285955200e8b749e7c3db978dcb4))
* implement configuration management system with automated template generation and initialize FastMCP server with lifespan management ([9e20a3e](https://github.com/ayato-labs/LogicHive/commit/9e20a3e4516380aa5d3be3ec4560407a1b23079c))
* implement core infrastructure, database integration, and CI/CD pipelines for LogicHive. ([ba47d5b](https://github.com/ayato-labs/LogicHive/commit/ba47d5b3c0a4e2e3495ee8d8178477887054d07e))
* implement core logic framework with multi-provider AI evaluation and orchestration services ([1b15602](https://github.com/ayato-labs/LogicHive/commit/1b15602f8cf003fdd715e0fe80de032d24df5e0b))
* implement environment-based configuration loading and structured logging configuration ([b0053d2](https://github.com/ayato-labs/LogicHive/commit/b0053d251343e5353c1f028b308faee3146008e0))
* implement ephemeral python executor with uv integration and resource monitoring ([d4f15fb](https://github.com/ayato-labs/LogicHive/commit/d4f15fb161381c15431a3a426bb98d9ee67d0713))
* implement EphemeralPythonExecutor using uv with resource monitoring and environment pooling ([cc5ed93](https://github.com/ayato-labs/LogicHive/commit/cc5ed9392ea88b4620c15f7b3d0d56a0c7bdfda8))
* implement FastMCP server with tools for function search, retrieval, saving, and database debugging ([8a4ecdb](https://github.com/ayato-labs/LogicHive/commit/8a4ecdb0f1a86dbb861edd920945bb1c703efdb6))
* implement Flet-based dashboard for settings management and system integrity diagnostics ([2a66e12](https://github.com/ayato-labs/LogicHive/commit/2a66e1205bacd9b8de9677c3cae38eeee8b8a5e8))
* implement Flet-based settings and diagnostic dashboard for configuration and system integrity checks ([7f1a328](https://github.com/ayato-labs/LogicHive/commit/7f1a3282a43eb4eb958ae4ed52e10c5e19e9b91c))
* implement LogicIntelligence engine for AI-powered code quality evaluation and embedding generation ([92817ea](https://github.com/ayato-labs/LogicHive/commit/92817eaac98ddfd9cc7c2b2656b8ff1a1b545e72))
* implement MCP server and settings UI for LogicHive orchestration ([7eec011](https://github.com/ayato-labs/LogicHive/commit/7eec01161f15ac865f1a075dc76af9430aad535a))
* implement MCP server with tool definitions for code search, retrieval, and validation ([1a6dacf](https://github.com/ayato-labs/LogicHive/commit/1a6dacfec2b5a7342cdeff6b5b5ad1acf8de20ce))
* implement MCP server with tool definitions for code search, retrieval, validation, and database debugging ([2e6e2bf](https://github.com/ayato-labs/LogicHive/commit/2e6e2bf803706e12f93cdd1d9efb1be5207db9ba))
* implement MCP server with tool definitions for code search, retrieval, validation, and database debugging ([78611be](https://github.com/ayato-labs/LogicHive/commit/78611be8080bba295a84598e888a2e4c0564265c))
* implement MCP server with tool definitions for LogicHive repository operations and initialize workspace infrastructure ([17e849e](https://github.com/ayato-labs/LogicHive/commit/17e849eebf87747183b2722e8422ca108b6b18c1))
* implement MCP server with tool registration and introduce background pool management for execution environments ([9012bfe](https://github.com/ayato-labs/LogicHive/commit/9012bfe98604dae16e6639337d726292fb9b2e61))
* implement modular configuration management and add automated CI/CD pipeline for binary builds ([9f048cf](https://github.com/ayato-labs/LogicHive/commit/9f048cf44f78e4caf7ee6080d4f01c5886107a69))
* implement modular configuration management and initialize FastMCP server structure ([f93e843](https://github.com/ayato-labs/LogicHive/commit/f93e8439bbd7d047df313f7f7935621dbe195010))
* implement multi-provider embedding service, logging infrastructure, and MCP server boilerplate ([0ea6e63](https://github.com/ayato-labs/LogicHive/commit/0ea6e63b67df295b0cb7bc6593790503165a1fbd))
* implement persistent FAISS vector index manager with incremental updates and automatic cleanup ([849cf5f](https://github.com/ayato-labs/LogicHive/commit/849cf5ffccc0e726bfac88d234e20fa125c4e36a))
* implement persistent vector index management using FAISS with automatic rebuilding and disk synchronization. ([e276577](https://github.com/ayato-labs/LogicHive/commit/e27657787a324defe382f9a618926aa7b8461422))
* implement secure local-only host binding and mDNS discovery for MCP server ([0c371f1](https://github.com/ayato-labs/LogicHive/commit/0c371f15d2fd599a33dfe96449580c7d21363c6f))
* implement Streamable HTTP transport and initialize base MCP server structure ([ecdf216](https://github.com/ayato-labs/LogicHive/commit/ecdf21694c3eabab66dcd906f99e38d704429cc9))
* implement structured JSON logging with loguru and add MCP server foundation ([13e3da5](https://github.com/ayato-labs/LogicHive/commit/13e3da55f698394f5bf581a6f52f58e9e0197b95))
* implement structured logging with loguru and add initial MCP server architecture with port conflict documentation ([a1d4564](https://github.com/ayato-labs/LogicHive/commit/a1d45644fff99d875f80170c5b9541ba045aa05a))
* implement system fingerprinting and PyInstaller build configuration for executable packaging ([1081c66](https://github.com/ayato-labs/LogicHive/commit/1081c6612050bc615c01f865a1c39d8909162f3e))
* implement system fingerprinting to detect and warn about environment drift in logic assets ([0764957](https://github.com/ayato-labs/LogicHive/commit/076495713a7b892cc748898d9e9dc858277fd547))
* implement tiered .env configuration loader and unified Loguru-based logging system ([4875765](https://github.com/ayato-labs/LogicHive/commit/48757656fcf07414e3f5cfe7a1002542df5bc271))
* implement tiered .env resolution with automatic home dir creation ([940092e](https://github.com/ayato-labs/LogicHive/commit/940092eca019202ac3cece81c4ddfcd861c78682))
* implement tiered configuration loading and add utility to list Gemini models ([d2673d7](https://github.com/ayato-labs/LogicHive/commit/d2673d70fb5b1e1f9028fa128d9420f0b6bbce6f))
* implement tiered configuration loading system and initialize MCP server infrastructure ([e0e844d](https://github.com/ayato-labs/LogicHive/commit/e0e844d1e8606d281723a1b540cc74d69dcb4c32))
* implement tiered configuration management with automatic .env generation and validation helpers ([6f12de3](https://github.com/ayato-labs/LogicHive/commit/6f12de3e010aac1a45cfb791b349d033e7bc8c13))
* initialize application logging directory and structured event log file ([b2229a0](https://github.com/ayato-labs/LogicHive/commit/b2229a042ad6d1d84ec3bdd7b71cf5e6a41120ec))
* initialize core configuration and project logging infrastructure ([e2066fb](https://github.com/ayato-labs/LogicHive/commit/e2066fb777faf7a6066946be542ae1a7e2bf2a26))
* initialize FastMCP server with tools for searching, retrieving, and saving functions in LogicHive ([54af9de](https://github.com/ayato-labs/LogicHive/commit/54af9deb9693b784e473bdec963b6d5cec258f0c))
* initialize project structure with core configuration, MCP server scaffolding, and architectural documentation ([b1d4948](https://github.com/ayato-labs/LogicHive/commit/b1d49488549eaf01cd2cde8a776e9d86636b4fa1))
* initialize system logging and database schema for LogicHive service ([a951451](https://github.com/ayato-labs/LogicHive/commit/a9514516b12739435da2771e0082c0219dae905e))
* initialize system logging and SQLite database schema for LogicHive ([3187eec](https://github.com/ayato-labs/LogicHive/commit/3187eec655d719c227e2a2c9d9b3176a512b3e04))
* migrate MCP transport from Stdio to Streamable HTTP and implement FastAPI server support. ([c59d5c7](https://github.com/ayato-labs/LogicHive/commit/c59d5c733a17701cee9d9ff3ee0941063c14f086))
* secure host by default and add setup wizard for network sharing configuration ([4ae1572](https://github.com/ayato-labs/LogicHive/commit/4ae1572744ebef5ef77c1590c648d6a4b7e50ec3))

# [0.10.0-dev.7](https://github.com/ayato-labs/LogicHive/compare/v0.10.0-dev.6...v0.10.0-dev.7) (2026-05-31)


### Bug Fixes

* **ci:** add write permissions to CLA check workflow ([d1ba8eb](https://github.com/ayato-labs/LogicHive/commit/d1ba8eb3f4c0db50623e30d529e532f2fd589058))

# [0.10.0-dev.6](https://github.com/ayato-labs/LogicHive/compare/v0.10.0-dev.5...v0.10.0-dev.6) (2026-05-31)


### Bug Fixes

* **ci:** ensure versioned pre-releases capture executables by fixing output logic ([ec1d8dd](https://github.com/ayato-labs/LogicHive/commit/ec1d8dda4fb71f4639f0ecdef84d7d919852bacc))

# [0.10.0-dev.5](https://github.com/ayato-labs/LogicHive/compare/v0.10.0-dev.4...v0.10.0-dev.5) (2026-05-31)


### Bug Fixes

* **build:** resolve PyInstaller metadata discovery failure and align binary names ([507951f](https://github.com/ayato-labs/LogicHive/commit/507951f1956757ed9da3ba3ef4e526d246f1d52e))

# [0.10.0-dev.4](https://github.com/ayato-labs/LogicHive/compare/v0.10.0-dev.3...v0.10.0-dev.4) (2026-05-31)


### Features

* add CI/CD pipeline for automated testing, semantic versioning, and Windows executable builds ([eccb10e](https://github.com/ayato-labs/LogicHive/commit/eccb10e37a9a8a2d55ab1f05cff9c448bddb7b90))

# [0.10.0-dev.3](https://github.com/ayato-labs/LogicHive/compare/v0.10.0-dev.2...v0.10.0-dev.3) (2026-05-31)


### Features

* add centralized logging configuration and implement core MCP server infrastructure ([f270318](https://github.com/ayato-labs/LogicHive/commit/f270318fc6d08e8f5cc04b65bfc0c3bfdcfe3f96))
* add diagnostic scripts to test Flet port configuration and module imports ([f7ccf43](https://github.com/ayato-labs/LogicHive/commit/f7ccf430b2371d721644413e63b949a38bc95afb))
* add Flet-based GUI for system configuration and integrity diagnostics ([1dc8138](https://github.com/ayato-labs/LogicHive/commit/1dc81383b598d78bf7155ac8240f102ca38ba67e))
* add Flet-based settings UI and generate PyInstaller build specifications for hub and settings binaries. ([fdc0458](https://github.com/ayato-labs/LogicHive/commit/fdc045801e54acc100d568ee2d3fdd97dfaaa6d4))
* add PoolManager to pre-warm virtual environments and reduce cold start latency ([c0fd7f6](https://github.com/ayato-labs/LogicHive/commit/c0fd7f6955295e9981ae25931da82d31ee1fa8f4))
* add PyInstaller spec file for building LogicHive hub and settings binaries ([2a43909](https://github.com/ayato-labs/LogicHive/commit/2a43909d2e155fd977ddb7e1008c3730242e7480))
* add PyInstaller spec file to bundle hub and settings binaries ([db6adca](https://github.com/ayato-labs/LogicHive/commit/db6adca1c75f1efe94eb65f8140a1c51fd6c3cab))
* implement asynchronous environment pool manager to eliminate cold start latency ([936fc56](https://github.com/ayato-labs/LogicHive/commit/936fc5625def407a73d8e9f09c51c3545054828c))
* implement comprehensive unit, chaos, and integration test suite with supporting configuration fixtures ([692bd5e](https://github.com/ayato-labs/LogicHive/commit/692bd5ed20b2f3d70f25c5ef61c2ae11ebc799b5))
* implement comprehensive unit, integration, and chaos test suites for code evaluation and system resilience ([5ab9697](https://github.com/ayato-labs/LogicHive/commit/5ab96978f73e285955200e8b749e7c3db978dcb4))
* implement core infrastructure, database integration, and CI/CD pipelines for LogicHive. ([ba47d5b](https://github.com/ayato-labs/LogicHive/commit/ba47d5b3c0a4e2e3495ee8d8178477887054d07e))
* implement core logic framework with multi-provider AI evaluation and orchestration services ([1b15602](https://github.com/ayato-labs/LogicHive/commit/1b15602f8cf003fdd715e0fe80de032d24df5e0b))
* implement ephemeral python executor with uv integration and resource monitoring ([d4f15fb](https://github.com/ayato-labs/LogicHive/commit/d4f15fb161381c15431a3a426bb98d9ee67d0713))
* implement EphemeralPythonExecutor using uv with resource monitoring and environment pooling ([cc5ed93](https://github.com/ayato-labs/LogicHive/commit/cc5ed9392ea88b4620c15f7b3d0d56a0c7bdfda8))
* implement FastMCP server with tools for function search, retrieval, saving, and database debugging ([8a4ecdb](https://github.com/ayato-labs/LogicHive/commit/8a4ecdb0f1a86dbb861edd920945bb1c703efdb6))
* implement Flet-based dashboard for settings management and system integrity diagnostics ([2a66e12](https://github.com/ayato-labs/LogicHive/commit/2a66e1205bacd9b8de9677c3cae38eeee8b8a5e8))
* implement Flet-based settings and diagnostic dashboard for configuration and system integrity checks ([7f1a328](https://github.com/ayato-labs/LogicHive/commit/7f1a3282a43eb4eb958ae4ed52e10c5e19e9b91c))
* implement MCP server and settings UI for LogicHive orchestration ([7eec011](https://github.com/ayato-labs/LogicHive/commit/7eec01161f15ac865f1a075dc76af9430aad535a))
* implement MCP server with tool definitions for code search, retrieval, and validation ([1a6dacf](https://github.com/ayato-labs/LogicHive/commit/1a6dacfec2b5a7342cdeff6b5b5ad1acf8de20ce))
* implement MCP server with tool definitions for code search, retrieval, validation, and database debugging ([2e6e2bf](https://github.com/ayato-labs/LogicHive/commit/2e6e2bf803706e12f93cdd1d9efb1be5207db9ba))
* implement MCP server with tool definitions for LogicHive repository operations and initialize workspace infrastructure ([17e849e](https://github.com/ayato-labs/LogicHive/commit/17e849eebf87747183b2722e8422ca108b6b18c1))
* implement MCP server with tool registration and introduce background pool management for execution environments ([9012bfe](https://github.com/ayato-labs/LogicHive/commit/9012bfe98604dae16e6639337d726292fb9b2e61))
* implement modular configuration management and initialize FastMCP server structure ([f93e843](https://github.com/ayato-labs/LogicHive/commit/f93e8439bbd7d047df313f7f7935621dbe195010))
* implement persistent FAISS vector index manager with incremental updates and automatic cleanup ([849cf5f](https://github.com/ayato-labs/LogicHive/commit/849cf5ffccc0e726bfac88d234e20fa125c4e36a))
* implement persistent vector index management using FAISS with automatic rebuilding and disk synchronization. ([e276577](https://github.com/ayato-labs/LogicHive/commit/e27657787a324defe382f9a618926aa7b8461422))
* implement secure local-only host binding and mDNS discovery for MCP server ([0c371f1](https://github.com/ayato-labs/LogicHive/commit/0c371f15d2fd599a33dfe96449580c7d21363c6f))
* implement Streamable HTTP transport and initialize base MCP server structure ([ecdf216](https://github.com/ayato-labs/LogicHive/commit/ecdf21694c3eabab66dcd906f99e38d704429cc9))
* implement structured JSON logging with loguru and add MCP server foundation ([13e3da5](https://github.com/ayato-labs/LogicHive/commit/13e3da55f698394f5bf581a6f52f58e9e0197b95))
* implement structured logging with loguru and add initial MCP server architecture with port conflict documentation ([a1d4564](https://github.com/ayato-labs/LogicHive/commit/a1d45644fff99d875f80170c5b9541ba045aa05a))
* implement tiered .env configuration loader and unified Loguru-based logging system ([4875765](https://github.com/ayato-labs/LogicHive/commit/48757656fcf07414e3f5cfe7a1002542df5bc271))
* implement tiered configuration management with automatic .env generation and validation helpers ([6f12de3](https://github.com/ayato-labs/LogicHive/commit/6f12de3e010aac1a45cfb791b349d033e7bc8c13))
* initialize application logging directory and structured event log file ([b2229a0](https://github.com/ayato-labs/LogicHive/commit/b2229a042ad6d1d84ec3bdd7b71cf5e6a41120ec))
* initialize project structure with core configuration, MCP server scaffolding, and architectural documentation ([b1d4948](https://github.com/ayato-labs/LogicHive/commit/b1d49488549eaf01cd2cde8a776e9d86636b4fa1))
* initialize system logging and database schema for LogicHive service ([a951451](https://github.com/ayato-labs/LogicHive/commit/a9514516b12739435da2771e0082c0219dae905e))
* migrate MCP transport from Stdio to Streamable HTTP and implement FastAPI server support. ([c59d5c7](https://github.com/ayato-labs/LogicHive/commit/c59d5c733a17701cee9d9ff3ee0941063c14f086))
* secure host by default and add setup wizard for network sharing configuration ([4ae1572](https://github.com/ayato-labs/LogicHive/commit/4ae1572744ebef5ef77c1590c648d6a4b7e50ec3))

# [0.10.0-dev.2](https://github.com/ayato-labs/LogicHive/compare/v0.10.0-dev.1...v0.10.0-dev.2) (2026-05-26)


### Features

* implement configuration management system with automated template generation and initialize FastMCP server with lifespan management ([9e20a3e](https://github.com/ayato-labs/LogicHive/commit/9e20a3e4516380aa5d3be3ec4560407a1b23079c))
* implement environment-based configuration loading and structured logging configuration ([b0053d2](https://github.com/ayato-labs/LogicHive/commit/b0053d251343e5353c1f028b308faee3146008e0))
* implement tiered configuration loading system and initialize MCP server infrastructure ([e0e844d](https://github.com/ayato-labs/LogicHive/commit/e0e844d1e8606d281723a1b540cc74d69dcb4c32))
* initialize FastMCP server with tools for searching, retrieving, and saving functions in LogicHive ([54af9de](https://github.com/ayato-labs/LogicHive/commit/54af9deb9693b784e473bdec963b6d5cec258f0c))

# [0.10.0-dev.1](https://github.com/ayato-labs/LogicHive/compare/v0.9.8...v0.10.0-dev.1) (2026-05-26)


### Bug Fixes

* **ci:** bypass astral-sh/setup-uv action due to download failures ([e874b60](https://github.com/ayato-labs/LogicHive/commit/e874b606fb9461c45be7d5001e47b31118f61c40))
* **ci:** set LOGICHIVE_TESTING=true to skip API key validation during tests ([e08bd6a](https://github.com/ayato-labs/LogicHive/commit/e08bd6aac06b738a52946b6db87c827a4e7926b8))
* **config:** ensure LOGICHIVE_TESTING correctly bypasses GEMINI_API_KEY check ([c2c8de0](https://github.com/ayato-labs/LogicHive/commit/c2c8de004cbbdd7b48b5f9c8a265d0722577730e))
* correct development branch name from 'dev' to 'develop' ([57d2e85](https://github.com/ayato-labs/LogicHive/commit/57d2e857b92bbbc089a3ca654ddcc766600d608d))


### Features

* add CI/CD pipeline for automated testing, semantic versioning, and Windows executable builds ([7d97c55](https://github.com/ayato-labs/LogicHive/commit/7d97c55a79b5f901407b969e6bc434f7c305a90c))
* automate pre-releases for develop branch with specialized binary naming ([d063613](https://github.com/ayato-labs/LogicHive/commit/d06361314a3a1a7fc697c7f9ea35e48537f25db8))
* enable continuous pre-release builds for develop branch and update config loader for executable compatibility ([596e99f](https://github.com/ayato-labs/LogicHive/commit/596e99f3711bf26578d72849f8756fc1d1998d3c))
* implement centralized configuration management and structured logging system ([4cd0abe](https://github.com/ayato-labs/LogicHive/commit/4cd0abe24da4db4a4ca7546050c27bb394743782))
* implement LogicIntelligence engine for AI-powered code quality evaluation and embedding generation ([92817ea](https://github.com/ayato-labs/LogicHive/commit/92817eaac98ddfd9cc7c2b2656b8ff1a1b545e72))
* implement MCP server with tool definitions for code search, retrieval, validation, and database debugging ([78611be](https://github.com/ayato-labs/LogicHive/commit/78611be8080bba295a84598e888a2e4c0564265c))
* implement modular configuration management and add automated CI/CD pipeline for binary builds ([9f048cf](https://github.com/ayato-labs/LogicHive/commit/9f048cf44f78e4caf7ee6080d4f01c5886107a69))
* implement multi-provider embedding service, logging infrastructure, and MCP server boilerplate ([0ea6e63](https://github.com/ayato-labs/LogicHive/commit/0ea6e63b67df295b0cb7bc6593790503165a1fbd))
* implement system fingerprinting and PyInstaller build configuration for executable packaging ([1081c66](https://github.com/ayato-labs/LogicHive/commit/1081c6612050bc615c01f865a1c39d8909162f3e))
* implement system fingerprinting to detect and warn about environment drift in logic assets ([0764957](https://github.com/ayato-labs/LogicHive/commit/076495713a7b892cc748898d9e9dc858277fd547))
* implement tiered .env resolution with automatic home dir creation ([940092e](https://github.com/ayato-labs/LogicHive/commit/940092eca019202ac3cece81c4ddfcd861c78682))
* implement tiered configuration loading and add utility to list Gemini models ([d2673d7](https://github.com/ayato-labs/LogicHive/commit/d2673d70fb5b1e1f9028fa128d9420f0b6bbce6f))
* initialize core configuration and project logging infrastructure ([e2066fb](https://github.com/ayato-labs/LogicHive/commit/e2066fb777faf7a6066946be542ae1a7e2bf2a26))
* initialize system logging and SQLite database schema for LogicHive ([3187eec](https://github.com/ayato-labs/LogicHive/commit/3187eec655d719c227e2a2c9d9b3176a512b3e04))

# [0.10.0.dev1](https://github.com/ayato-labs/LogicHive/compare/v0.9.8...v0.10.0.dev1) (2026-05-26)


### Bug Fixes

* **ci:** bypass astral-sh/setup-uv action due to download failures ([e874b60](https://github.com/ayato-labs/LogicHive/commit/e874b606fb9461c45be7d5001e47b31118f61c40))
* **ci:** set LOGICHIVE_TESTING=true to skip API key validation during tests ([e08bd6a](https://github.com/ayato-labs/LogicHive/commit/e08bd6aac06b738a52946b6db87c827a4e7926b8))
* **config:** ensure LOGICHIVE_TESTING correctly bypasses GEMINI_API_KEY check ([c2c8de0](https://github.com/ayato-labs/LogicHive/commit/c2c8de004cbbdd7b48b5f9c8a265d0722577730e))
* correct development branch name from 'dev' to 'develop' ([57d2e85](https://github.com/ayato-labs/LogicHive/commit/57d2e857b92bbbc089a3ca654ddcc766600d608d))


### Features

* add CI/CD pipeline for automated testing, semantic versioning, and Windows executable builds ([7d97c55](https://github.com/ayato-labs/LogicHive/commit/7d97c55a79b5f901407b969e6bc434f7c305a90c))
* automate pre-releases for develop branch with specialized binary naming ([d063613](https://github.com/ayato-labs/LogicHive/commit/d06361314a3a1a7fc697c7f9ea35e48537f25db8))
* enable continuous pre-release builds for develop branch and update config loader for executable compatibility ([596e99f](https://github.com/ayato-labs/LogicHive/commit/596e99f3711bf26578d72849f8756fc1d1998d3c))
* implement centralized configuration management and structured logging system ([4cd0abe](https://github.com/ayato-labs/LogicHive/commit/4cd0abe24da4db4a4ca7546050c27bb394743782))
* implement LogicIntelligence engine for AI-powered code quality evaluation and embedding generation ([92817ea](https://github.com/ayato-labs/LogicHive/commit/92817eaac98ddfd9cc7c2b2656b8ff1a1b545e72))
* implement modular configuration management and add automated CI/CD pipeline for binary builds ([9f048cf](https://github.com/ayato-labs/LogicHive/commit/9f048cf44f78e4caf7ee6080d4f01c5886107a69))
* implement multi-provider embedding service, logging infrastructure, and MCP server boilerplate ([0ea6e63](https://github.com/ayato-labs/LogicHive/commit/0ea6e63b67df295b0cb7bc6593790503165a1fbd))
* implement tiered .env resolution with automatic home dir creation ([940092e](https://github.com/ayato-labs/LogicHive/commit/940092eca019202ac3cece81c4ddfcd861c78682))
* implement tiered configuration loading and add utility to list Gemini models ([d2673d7](https://github.com/ayato-labs/LogicHive/commit/d2673d70fb5b1e1f9028fa128d9420f0b6bbce6f))
* initialize core configuration and project logging infrastructure ([e2066fb](https://github.com/ayato-labs/LogicHive/commit/e2066fb777faf7a6066946be542ae1a7e2bf2a26))
* initialize system logging and SQLite database schema for LogicHive ([3187eec](https://github.com/ayato-labs/LogicHive/commit/3187eec655d719c227e2a2c9d9b3176a512b3e04))

## [0.9.8](https://github.com/ayato-labs/LogicHive/compare/v0.9.7...v0.9.8) (2026-05-24)


### Bug Fixes

* make .env resolution robust and explicit ([cf17bf6](https://github.com/ayato-labs/LogicHive/commit/cf17bf673ad9f957080623ec8007f7fe8cb6db32))

## [0.9.7](https://github.com/ayato-labs/LogicHive/compare/v0.9.6...v0.9.7) (2026-05-24)


### Bug Fixes

* correctly handle semantic-release outputs ([b0142b1](https://github.com/ayato-labs/LogicHive/commit/b0142b16073b561633e2f847bb2c0dc0aa4bc64e))

## [0.9.6](https://github.com/ayato-labs/LogicHive/compare/v0.9.5...v0.9.6) (2026-05-24)


### Bug Fixes

* correct google.genai hidden imports in spec file ([8551740](https://github.com/ayato-labs/LogicHive/commit/8551740552c4cdc794e04b73a9fab139da2a9751))

## [0.9.5](https://github.com/ayato-labs/LogicHive/compare/v0.9.4...v0.9.5) (2026-05-24)


### Bug Fixes

* remove invalid CLI flag from PyInstaller command ([70c625c](https://github.com/ayato-labs/LogicHive/commit/70c625ca2f9bc5816cdb33d973280ae4eeffc6e6))

## [0.9.4](https://github.com/ayato-labs/LogicHive/compare/v0.9.3...v0.9.4) (2026-05-24)


### Bug Fixes

* explicitly include google-genai hidden-import for PyInstaller ([be740da](https://github.com/ayato-labs/LogicHive/commit/be740dab65d15af589b91f492d17381db30e7804))

## [0.9.3](https://github.com/ayato-labs/LogicHive/compare/v0.9.2...v0.9.3) (2026-05-24)


### Bug Fixes

* use sys.argv[0] instead of __file__ in spec file ([fa9a642](https://github.com/ayato-labs/LogicHive/commit/fa9a642264727676d6b27d775bca068ce6ff27ff))

## [0.9.2](https://github.com/ayato-labs/LogicHive/compare/v0.9.1...v0.9.2) (2026-05-24)


### Bug Fixes

* use absolute path in PyInstaller spec ([4011063](https://github.com/ayato-labs/LogicHive/commit/4011063caee8c53a31a02a3d029a3b8eec83c3f0))

## [0.9.1](https://github.com/ayato-labs/LogicHive/compare/v0.9.0...v0.9.1) (2026-05-24)


### Bug Fixes

* force output detection for semantic-release ([78b2c6e](https://github.com/ayato-labs/LogicHive/commit/78b2c6e1454724b65e67c641e04f3a097dd701da))

# [0.9.0](https://github.com/ayato-labs/LogicHive/compare/v0.8.0...v0.9.0) (2026-05-24)


### Bug Fixes

* adopt uv run/sync based workflow for CI/CD environment isolation ([0cb4fa9](https://github.com/ayato-labs/LogicHive/commit/0cb4fa9a7045ad0a0a0bd13ee3667fe093697a7f))
* **ci:** add diagnostic job to verify trigger ([4350312](https://github.com/ayato-labs/LogicHive/commit/43503122764266e6baf5aec424f69c174f7b8667))
* **ci:** correct .exe build path and environment in GitHub Actions ([43fffe9](https://github.com/ayato-labs/LogicHive/commit/43fffe912755803a27cc29d7d9e176a934c60a7e))
* **ci:** exclude exports directory from ruff linting ([f083371](https://github.com/ayato-labs/LogicHive/commit/f08337190d96a0361c28163fa4e8910236dd2bf6))
* **ci:** rename workflow file to resolve trigger issues ([101bceb](https://github.com/ayato-labs/LogicHive/commit/101bcebd4517fabc01c891e1c6ae41967f06ad59))
* **ci:** scope ruff linting to core directories only ([6f5ae8e](https://github.com/ayato-labs/LogicHive/commit/6f5ae8e050fef5c056f320b54f78300f78112ad7))
* **ci:** strictly scope ruff linting to src and tests ([924e0a1](https://github.com/ayato-labs/LogicHive/commit/924e0a1d28631aae02a3d10600e5b4f3377beb4e))
* **ci:** trigger workflow update after repository move ([291b88e](https://github.com/ayato-labs/LogicHive/commit/291b88e2021522a70743ba89c109070c7e11b6ec))
* comprehensive CI stability fix (metadata, imports, and smarter AI mocking) ([8165149](https://github.com/ayato-labs/LogicHive/commit/8165149d15929f50bb0a06eeaf306a32bdec7de4))
* correct global mock patch paths to avoid test setup errors ([1f7677e](https://github.com/ayato-labs/LogicHive/commit/1f7677ed05638cf910f31f9ef2a3bd7897460ae0))
* correct signature of mock_evaluate_all in global AI mock ([b751320](https://github.com/ayato-labs/LogicHive/commit/b7513201090cc669d40870b66dc37f88fc25f7d7))
* decouple python executor unit test from network dependency ([36ddf8e](https://github.com/ayato-labs/LogicHive/commit/36ddf8e74de5bc7ffc42d1f982b4028fa2218d3d))
* final architectural cleanup and syntax mock hardening ([de26b3f](https://github.com/ayato-labs/LogicHive/commit/de26b3f211b131b01aed8b59bb8c075512c4ae57))
* final precision adjustments for CI/CD compatibility ([277219a](https://github.com/ayato-labs/LogicHive/commit/277219ac2abfeacf6c6fed3fdd87f56db237b9b5))
* force release to verify corrected exe build workflow ([f597195](https://github.com/ayato-labs/LogicHive/commit/f597195f6c2fcc5935f34d42888a8f27554c36e0))
* global AI mocking for test stability and enhanced CI debug logging ([9acf64a](https://github.com/ayato-labs/LogicHive/commit/9acf64afe38c51425602cd561ef83a4bd5fe70bd))
* import os and clean up whitespace in test ([9a557b0](https://github.com/ayato-labs/LogicHive/commit/9a557b0e172d1fe47cfd23d8b63ee5cbcbd052ce))
* **lint:** resolve ruff complexity (C901) and simplicity (SIM) violations ([75539aa](https://github.com/ayato-labs/LogicHive/commit/75539aaee8dd178d114b06dd45e41828af7d2b2e))
* remove unnecessary npm install in CI ([dbf9d9f](https://github.com/ayato-labs/LogicHive/commit/dbf9d9fbde3df785998fba2e98075da52dc1026e))
* resolve GH Action test failures ([2eb9b7c](https://github.com/ayato-labs/LogicHive/commit/2eb9b7c93afee256977e214f4ffe56e4a388d316))
* resolve global linting errors and E402 imports in tests ([395d33c](https://github.com/ayato-labs/LogicHive/commit/395d33c7aaa70a60ec47bcf0c72a700f753e3d80))
* resolve import sorting and unused variable ([d5c93ec](https://github.com/ayato-labs/LogicHive/commit/d5c93ecaec47994b72021b11cfd3dc8b65dbc010))
* resolve linting errors in test file ([6ad1583](https://github.com/ayato-labs/LogicHive/commit/6ad1583e4faf4fddc3fff35969a335d0419d1b8d))
* resolve NameError in get_function and sync AI mocks for call tracking ([0d0602e](https://github.com/ayato-labs/LogicHive/commit/0d0602e9b2d4b16498647c1313e8060b1d7b0d8f))
* resolve NameErrors and refactor test_db for robust CI execution ([615e2ec](https://github.com/ayato-labs/LogicHive/commit/615e2ecdff4d37968da1b684fb820d9dce70befa))
* resolve test collection errors and gracefully skip real API tests in CI ([50faa6a](https://github.com/ayato-labs/LogicHive/commit/50faa6a32e1aa244a142e83a4ce40a8c18d5dea8))
* resolve test regression in consolidation unit and fix typo in document construction ([0ba2894](https://github.com/ayato-labs/LogicHive/commit/0ba2894c54257943e363d2717034c00602c69c42))
* resolve zombie process and uv offline mode resolution errors ([#14](https://github.com/ayato-labs/LogicHive/issues/14)) ([d5b438f](https://github.com/ayato-labs/LogicHive/commit/d5b438f64c3a89fd7fd820b40923acd78909f7ad))
* restore architectural integrity and resolve final validation bugs ([84a65ce](https://github.com/ayato-labs/LogicHive/commit/84a65cee2022ddc6d3bedbf1b00acc1d46ab4890))
* restore semantic-release dependencies and npm install step ([295f286](https://github.com/ayato-labs/LogicHive/commit/295f286f090f336f715f26a5818cc08651ad9832))
* use --system flag for uv pip install and enable Node 24 support ([e33d46e](https://github.com/ayato-labs/LogicHive/commit/e33d46e9990c4b3ef4a2bd36ae6bd5682e270b71))
* use portable python print for status.txt to ensure encoding consistency ([3da20df](https://github.com/ayato-labs/LogicHive/commit/3da20df46554a55e3e122d02805e80e307b12143))


### Features

* add DependencyVouchEvaluator and implement system-level chaos and timeout resilience tests ([007f2de](https://github.com/ayato-labs/LogicHive/commit/007f2de690af9124331c299e03f71b1e06c3a274))
* add DependencyVouchEvaluator to detect and validate hallucinated Python imports against project manifests ([db9fd11](https://github.com/ayato-labs/LogicHive/commit/db9fd11fbc6343e1cb27d7d045fb0c2f7bbe145e))
* add dogfooding script to test asset registration with resilient data fetcher implementation ([458be38](https://github.com/ayato-labs/LogicHive/commit/458be3891e6c07443a2edfbea7515c54382ddd37))
* add scratch scripts for testing async saving and vector index synchronization ([4f1c4b3](https://github.com/ayato-labs/LogicHive/commit/4f1c4b3ae20f4263391609819bf26003efaec97d))
* **core, tests:** stabilize test suite and implement phase 2 runtime verification ([3dbfafb](https://github.com/ayato-labs/LogicHive/commit/3dbfafb7e2af8e5d388a43cd22d74aef22af3789))
* dual distribution strategy with Windows EXE and OCI Container ([9254734](https://github.com/ayato-labs/LogicHive/commit/9254734a157643c1b547b43fe3e03228a9af9588))
* implement 3-tier testing suite and deterministic verification layer ([25adb76](https://github.com/ayato-labs/LogicHive/commit/25adb76a5074b4fcd5e40041a78e22b164febefa))
* implement Absolute Logic with AI Veto Power and Forensic Auditor persona ([ffb92c6](https://github.com/ayato-labs/LogicHive/commit/ffb92c66be86aa194a0736355e8e04277f64bf66))
* implement Deterministic Verification Layer with AST analysis (Fact over Opinion) ([97b4688](https://github.com/ayato-labs/LogicHive/commit/97b4688790f0ce1803f78936e009e8e94404249c))
* implement dynamic plugin-based evaluation manager with multi-layered scoring and security gates ([2a2af3f](https://github.com/ayato-labs/LogicHive/commit/2a2af3f57ad144147cedd910dc0c13ec7e1dcbc7))
* implement FastMCP server with tools for managing code assets in LogicHive ([14453e4](https://github.com/ayato-labs/LogicHive/commit/14453e43517c9db9ec3ad71e4013ba23394f11c1))
* implement logic hardening, docker isolation, and environmental fingerprinting ([14e88cd](https://github.com/ayato-labs/LogicHive/commit/14e88cdb2071df60252b4a58ddbae99b6b1df94d))
* implement MCP server and core logic utilities with dogfooding verification scripts ([05db26a](https://github.com/ayato-labs/LogicHive/commit/05db26a5699b09a6433c26f61adc8a38dbf0cbfe))
* implement MCP server with search, retrieval, and quality-gated storage tools ([430f192](https://github.com/ayato-labs/LogicHive/commit/430f192a3e78ae7d6f93be7bfe8ff5bb6b6514a0))
* implement orchestrator with integrated quality gate, dependency extraction, and automated asset management ([fb750a6](https://github.com/ayato-labs/LogicHive/commit/fb750a6274cbeb7a000f570f23fb1dd1a4e25463))
* implement orchestrator with quality gate evaluation, automated dependency extraction, and SQLite storage integration ([c6f49b2](https://github.com/ayato-labs/LogicHive/commit/c6f49b213a9e8167f48d4cf415759825aacac2cb))
* implement PoolManager for pre-warmed virtual environments and add SqliteStorage engine for persistent data management ([375a76b](https://github.com/ayato-labs/LogicHive/commit/375a76b9ef1033c738777dec4b30407b480ac8b3))
* implement PoolManager to provide pre-warmed virtual environments and integrate with MCP server lifecycle ([f8623ba](https://github.com/ayato-labs/LogicHive/commit/f8623ba22b08ca4c8f11c61e6d8bd42756df911d))
* implement rigorous database testing and migration integrity ([b146d3c](https://github.com/ayato-labs/LogicHive/commit/b146d3cad00e9388852bbaeb7201fe1b0d89107a))
* implement RuntimeEvaluator and EphemeralPythonExecutor with uv-based isolation and resource monitoring ([ab02eb7](https://github.com/ayato-labs/LogicHive/commit/ab02eb7daf3db437364924f28115f72f1a0e23f7))
* implement RuntimeEvaluator to execute code and verify tests in ephemeral environments ([dcd4440](https://github.com/ayato-labs/LogicHive/commit/dcd444082a0ae53a935d89ed71c360782121a9d9))
* implement SQLite storage engine and core evaluation framework with plugin support ([9fd455e](https://github.com/ayato-labs/LogicHive/commit/9fd455ebbabf71ad6a07bc3effc036fb257b9b56))
* implement SQLite storage layer with schema initialization, version history management, and resilience testing suite ([44052e9](https://github.com/ayato-labs/LogicHive/commit/44052e99072e3272f499ea7317af3002ead3280a))
* implement static security analysis plugin and FAISS-based vector storage system ([e5cf44c](https://github.com/ayato-labs/LogicHive/commit/e5cf44c7ec10eedf5015dc99696568ea077463ba))
* **infra:** harden stability, observability, and apply ruff formatting ([7b9648d](https://github.com/ayato-labs/LogicHive/commit/7b9648d7fd07ff37b7f8f31f33d3d832261b1096))
* **logging:** migrate to structured JSON logging via Loguru ([d864bd8](https://github.com/ayato-labs/LogicHive/commit/d864bd8b6f652600dc90818f6af1ffcf17fce206))
* make GitHub backup optional and decoupled (v0.5.1) ([9f2269a](https://github.com/ayato-labs/LogicHive/commit/9f2269a758a7a6f1d700bf9a84cb7c0acd01ccf2))
* overhaul testing architecture and expand CI matrix for dev branch ([7416609](https://github.com/ayato-labs/LogicHive/commit/7416609d317f8612486aa6a5022c5ab03cb0c03c))
* switch to Docker-based distribution and automate versioning with Semantic Release ([62bc110](https://github.com/ayato-labs/LogicHive/commit/62bc1103325f05d22ac6c8d4e89d5ddb883cf76b))
* upgrade to Rigorous Logic Gate to prevent quality theater ([64d188f](https://github.com/ayato-labs/LogicHive/commit/64d188f8934248a38551c9719492c4c213b053f7))


### Performance Improvements

* **pool:** optimize startup by parallelizing directory cleanup ([583759a](https://github.com/ayato-labs/LogicHive/commit/583759ad38642a1a8429b3e026718c0f00d55f61))
