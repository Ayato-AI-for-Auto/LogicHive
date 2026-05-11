![CD Pipeline](https://github.com/Ayato-AI-for-Auto/LogicHive/actions/workflows/cd.yml/badge.svg)
# 🛡️ LogicHive: Professional Logic Orchestration Infrastructure

> **"Stop rebuilding the same logic. Build a long-term intelligence asset."**  
> **哲学: 巨人の肩の上に乗り、真に価値ある創造に集中せよ。**

LogicHive is a professional-grade **Logic Orchestration Layer** that sits between AI agents (Antigravity, Cursor, Gemini) and your persistent knowledge vault. It stabilizes, verifies, and preserves logic as reusable "Atoms."

---

## 📖 Documentation Hub

- **[Architecture & Design Decisions](docs/architecture.md)**: The "Why" and "How" behind LogicHive.
- **[Usage Guide](docs/usage.md)**: How to integrate LogicHive into your workflow.
- **[Commercial Licensing](COMMERCIAL.md)**: Options for proprietary and SaaS use.
- **[Contribution Guidelines](CONTRIBUTING.md)**: How to help improve the Hive.

---

## 🧠 Philosophy: Logic over Sophistry (屁理屈に論理で抗う)

AI agents excel at creating code that *looks* correct (Sophistry). LogicHive is built on the belief that **"Opinion without proof is noise."**

### 🎯 Core Principles
- **Reusable Atoms**: Storing only the "Atomic Logic" that has been structurally verified.
- **Anti-Rot (Software Preservation)**: Ensuring code works today, and will work tomorrow via automated auditing.
- **Strategic Leverage**: Starting every project from "One step ahead" by standing on the shoulders of your past work.

---

## 🏗️ The Rigor Gate: A Hybrid Approach

LogicHive uses a **Hybrid Deterministic Gate** to veto non-factual AI opinions:
- **Fact (40%)**: AST analysis. Mandatory veto power (Assertion counting, Hollow logic detection).
- **Static (30%)**: Ruff/Radon metrics for code health.
- **AI (20%)**: Forensic auditing by LLMs.
- **Execution (10%)**: Isolated runtime validation.

---

## 🚀 Quick Setup

```powershell
# 1. Install dependencies
uv pip install -e .

# 2. Register MCP Server
uv run src/mcp_server.py
```

---

## 📄 License

LogicHive is dual-licensed:

- **OSS License**: [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE). Free for open-source use.
- **Commercial License**: For proprietary products and SaaS use without source disclosure. See [COMMERCIAL.md](COMMERCIAL.md) for details.

*Copyright (C) 2026 ayato-labs. All rights reserved.*

---

## 🇯🇵 日本語サマリー (Japanese Summary)

LogicHiveは、「仕様の再構築」や「冗長な実装」から開発者を解放するための**プロフェッショナル向けロジック・オーケストレーション・インフラ**です。

### 核心的な価値
- **死んだコードの撲滅**: 良質なロジックを「共有知」へ。
- **決定論的品質ゲート**: AIの温情を排し、AST解析(事実)が品質を担保する。
- **巨人の肩に乗る**: 書けば書くほど開発環境が強化される「知の資産化」。
- **デュアルライセンス**: OSSとしての普及と、商用利用での機密性保持を両立。
