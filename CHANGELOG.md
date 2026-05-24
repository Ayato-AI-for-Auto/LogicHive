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
