# Contributing to LogicHive

First off, thank you for considering contributing to LogicHive! We are excited to build a high-precision logic hub for AI agents together with the developer community.

LogicHive is developed under the **AGPL-3.0 License**. By contributing to this repository, you agree that your contributions will be licensed under the same license.

---

## How Can I Contribute?

### 1. Adding New Rigor Gate Evaluators
The core of LogicHive is its **Rigor Gate** quality evaluators found in `src/core/evaluation/plugins/`. You can contribute by writing new evaluators:
- Support for new languages (e.g., AST parsing for JavaScript, TypeScript, or Go).
- Integration of new static analysis linters (e.g., ESLint, Go Vet).
- Custom security static rules to catch vulnerable functions.

### 2. Enhancing Test Coverage
We employ a zero-tolerance policy for regression. We always welcome:
- Additional unit tests under `tests/unit/`.
- Dynamic sandboxing test suites under `tests/chaos/` to test edge cases.

### 3. Improving Documentation
- Improving `README.md` or translating conceptual documents.
- Adding architectural ideas to the `docs/idea/` folder.

---

## Local Development Setup

To set up a local development environment, make sure you have [uv](https://github.com/astral-sh/uv) installed:

```powershell
# 1. Clone the repository
git clone https://github.com/ayato-labs/LogicHive.git
cd LogicHive

# 2. Install dependencies in editable mode
uv pip install -e .

# 3. Create a local environment file
copy .env.example .env
# Edit .env and set your GEMINI_API_KEY for testing AI features
```

### Running the Test Suite

We use `pytest` for all test layers. Run the following command to verify everything works:

```powershell
uv run pytest
```

---

## Pull Request Guidelines

To maintain the high precision and reliability of the hub, please adhere to these rules when submitting a Pull Request:

1. **Link an Issue**: Every PR must solve an open issue. Please create or claim an issue before writing code.
2. **Include Tests**: If your PR modifies codebase logic, you **MUST** include corresponding unit or integration tests. PRs without test validation will be automatically rejected.
3. **Follow Linting Standards**: Run `ruff check .` before committing your changes.
