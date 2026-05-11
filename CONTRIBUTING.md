# 🤝 Contributing to LogicHive

We welcome contributions to LogicHive! To maintain a professional and legally compliant repository, please follow these guidelines.

## 🛡️ CLA Requirement
By contributing to this repository, you agree to the [LogicHive Contributor License Agreement (CLA)](CLA.md). 

**Action Required**: When submitting a Pull Request, please include the following statement in the description:
> I have read and agree to the CLA for LogicHive.

## 🏗️ Development Workflow

1. **Issue First**: Please create or comment on an issue before starting work.
2. **Branching**: Use `feat/` or `fix/` prefixes (e.g., `feat/123-add-new-gate`).
3. **Quality Gate**: All code must pass the **Rigor Gate** (Structural AST check + Tests).
   - Ensure your code has at least 3 assertions in the `test_code`.
   - Avoid "Hollow Logic" (methods with only `pass` or `...`).
4. **Linting**: We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

## 🧪 Testing Policy
"Opinion without proof is noise."
LogicHive is built on structural verification. Every contribution MUST include functional tests that prove the logic works in isolated environments.

## 📄 Licensing
All contributions will be licensed under the **AGPL-3.0** for the public and may be used in **Commercial Licenses** by ayato-labs.

---
*Happy Hacking in the Hive!*
