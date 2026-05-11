# Contributing to LogicHive

<<<<<<< HEAD
First off, thank you for considering contributing to LogicHive! It's people like you that make LogicHive such a great tool.

## Single-Vendor Open Source Model

LogicHive follows a **Single-Vendor Open Source (SV-COS)** model. This means that while the source code is public and open for contributions, the strategic direction and commercial rights are managed exclusively by Ayato Studio.

## Contributor License Agreement (CLA)

Before we can merge your pull request, you must agree to our [Contributor License Agreement (CLA)](CLA.md). This ensures that we can protect the project and its users while keeping it sustainable.

**How to agree**: Please include the following statement in your PR description:
> I have read and agree to the CLA for LogicHive.

## Contribution Guidelines

1.  **Bug Reports**: Please use the GitHub Issue tracker. Provide clear reproduction steps.
2.  **Feature Requests**: Open an issue first to discuss the feature before starting implementation.
3.  **Pull Requests**:
    -   Ensure the code follows the existing style.
    -   Add tests for any new logic.
    -   Reference any related issues.
    -   Include the CLA agreement statement.

## Code of Conduct

We expect all contributors to follow the spirit of the project: Professionalism, Respect, and Collaboration.

---
*Thank you for helping us liberate humans from mundane tasks!*
=======
We welcome contributions to LogicHive! To ensure the long-term sustainability and commercial viability of the project, we have established the following guidelines.

---

## 1. CLA Requirement

Before we can merge your pull request, you must agree to the **Contributor License Agreement (CLA)**. This ensures that ayato-labs has the rights to include your contribution in both the AGPL-3.0 and Commercial versions of LogicHive.

### How to agree
Please add the following line to your Pull Request description:

> I have read and agree to the CLA for LogicHive.

[Read the full CLA here](CLA.md)

---

## 2. Types of Contributions

| Type | Examples | Policy |
| :--- | :--- | :--- |
| **Accepting** | Bug fixes, Documentation, Tests | Merged after CLA check and review. |
| **Discussion Required** | New features, Architecture changes | Open an Issue first for discussion. |
| **Not Accepting** | Core proprietary logic, License changes | These are generally reserved for the core maintainer. |

---

## 3. Development Setup

LogicHive uses `uv` for dependency management.

```bash
# Clone the repository
git clone https://github.com/ayato-labs/LogicHive.git
cd LogicHive

# Install dependencies
uv sync

# Run tests
pytest
```

---

## 4. Code Quality

We use `ruff` for linting and formatting. Please ensure your code passes linting before submitting a PR.

```bash
ruff check .
ruff format .
```

---

*Thank you for helping us improve LogicHive!*
>>>>>>> c06c42a (feat: implement deterministic evaluation engine and project structure with robust testing and CLA compliance)
