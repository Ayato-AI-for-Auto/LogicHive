# ADR-0026: Multi-Language Execution and Evaluation Expansion

- **Date**: 2026-06-07
- **Status**: Proposed
- **Deciders**: ayato-labs (User), Antigravity (Agent)

## Context
LogicHive originally only supported Python code execution and verification.
To expand LogicHive to a versatile logic repository, we need support for major programming languages: JavaScript/TypeScript, Java, PHP, C, and HTML.

Each language has different execution runtimes, compilation pipelines, and static analysis requirements:
1. **JavaScript/TypeScript**: Runs via Node.js on the client.
2. **Java**: Requires JDK compilation (`javac`) and execution (`java`).
3. **PHP**: Script execution using PHP CLI.
4. **C**: Requires a C compiler (`gcc`, `clang`, or MSVC `cl`).
5. **HTML**: A markup language that does not "execute" but requires layout and syntax parsing validation.

Additionally, the client host might not have all runtimes (like `gcc` or `php`) installed. We must handle missing compiler/runtime exceptions gracefully without crashing LogicHive's verification service.

## Decision
We will extend `BaseExecutor` and implement new executors under the dynamic loading structure, utilizing the newly introduced `BaseSandbox` runner.

### 1. Executors
- **JavaScript/TypeScript (`javascript.py`)**: Spawns a harness file `harness.js` that loads the user code and test code, runs them via `node`, and captures output inside the sandboxed environment.
- **Java (`java.py`)**: Generates source files, compiles them using `javac`, and runs the resulting class file using `java` under the sandbox.
- **PHP (`php.py`)**: Runs syntax validation check `php -l` and executes script files under the sandbox if `php` CLI is found.
- **C (`c.py`)**: Searches the system for `gcc`, `clang`, or `cl`. Compiles the source, and runs the generated binary inside the sandbox.
- **HTML (`html.py`)**: Since HTML does not run as a backend script, the executor parses it using Python's standard `html.parser` to verify tag structural validity and nesting correctness.

### 2. Missing Runtime Graceful Fallbacks
If a compiler/interpreter (e.g. `gcc`, `php`) is missing, the executor will return an `ExecutionResult` with `ExecutionStatus.FAILURE` and a detailed stderr logs explanation:
> "Execution failed: Compiler/Runtime 'gcc' is not installed or not found in system PATH."

This prevents raw subprocess startup exceptions from bubbling up as internal engine errors.

### 3. Evaluation Plugins
- **Static checks (`static.py`)**: Add structural and bracket check validation for other languages.
- **Deterministic check (`deterministic.py`)**: Extend regex assertion count checks to support JS/TS, Java, PHP, and C syntax.

## Consequences
### Positive
- **Broad Language Coverage**: Allows saving and verifying logic in five new major languages.
- **Resiliency**: LogicHive remains fully functional even if some runtimes are missing.
- **Secure**: All scripting languages (JS, Java, PHP, C) leverage `WindowsNativeSandbox` for resource and process isolation.

### Negative / Risks
- **Testing Constraints**: Testing C and PHP execution in local tests is mocked or skipped if the local host lacks the compilers. This is acceptable and handled cleanly in the test suite.
