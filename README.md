# LogicHive (Professional AI Logic Hub)

🛡️ **LogicHive** is a high-precision knowledge extraction and logic management system. It enables AI agents to accumulate, verify, and reuse high-quality code assets via the Model Context Protocol (MCP).

> **"Stop rebuilding the same logic. Build a long-term intelligence asset."**  
> **哲学: 巨人の肩の上に乗り、真に価値ある創造に集中せよ。**

---

## 🏗️ The Rigor Gate: A Hybrid Approach

LogicHive uses a **Hybrid Deterministic Gate** to veto non-factual AI opinions:
- **Fact (40%)**: AST analysis. Mandatory veto power (Assertion counting, Hollow logic detection).
- **Static (30%)**: Ruff/Radon metrics for code health.
- **AI (20%)**: Forensic auditing by LLMs.
- **Execution (10%)**: Isolated runtime validation.

---

## 🌟 Key Features

- **Hybrid Knowledge Search**: Semantic and exact-match search for code patterns.
- **Verification Quality Gate**: Automated testing and linting before code is "vaulted".
- **MCP Integration**: Seamlessly expose complex logic to AI agents.
- **Project Isolation**: Manage logic assets across multiple namespaces and projects.

---

## 🚀 Workflow

1. **Discovery (探索)**: Find logic atoms via LogicHive MCP.
2. **Retrieval (抽出)**: Inject verified logic into the agent context.
3. **Adaptation (適合)**: AI refactors logic to match current namespaces.
4. **Professionalization (資産化)**: Refined logic is saved back.
5. **Stabilization (安定化)**: Background tools re-verify assets 24/7.

---

## 🐘 Handling Heavy AI Assets (Torch, Sklearn)

Registering code that imports large libraries like `torch` or `sklearn` can hit the **20s Quality Gate Timeout**. To bypass this and maintain a fast development rhythm, use the following patterns:

### 1. Lazy Import (Recommended)
Move heavy imports inside your functions. This prevents the library from loading during the initial module-level scan by LogicHive's AST analyzer.

### 2. Smart Mocking
If you must have top-level imports, use the `mock_imports` parameter in `save_function`. LogicHive will inject `MagicMock` for those modules during verification.

---

## 🚀 Quick Setup (Dual Distribution)

LogicHive offers two ways to run the server, completely circumventing any enterprise container licensing friction.

### Option A: Windows Native EXE (Zero Friction)
For Windows-heavy corporate environments, you do not need Docker at all.

1. Download `LogicHive-MCP.exe` from the [Latest Release](https://github.com/ayato-labs/LogicHive/releases).
2. Double-click the `.exe` (or run it via Command Prompt).
3. The server runs natively on `http://localhost:10880/sse`.

*Note: Because LogicHive uses network-based SSE, **a single Windows machine running the `.exe` can serve your entire team**—even if they are on Mac or Linux clients.*

### Option B: OCI Container (Docker / Podman)
LogicHive is also distributed as an **OCI-compliant Container Image** for cloud-native deployment.

> **Note on Licensing**: Because this is a standard OCI image, you can run it using 100% free alternatives like **Podman**, **Rancher Desktop**, or standard Docker Engine on Linux.

```bash
docker pull ghcr.io/ayato-labs/logichive-hub:latest

docker run -d \
  -p 10880:10880 \
  -e GEMINI_API_KEY=your_api_key_here \
  -v logichive_data:/app/storage/data \
  --name logichive-hub \
  ghcr.io/ayato-labs/logichive-hub:latest
```

### 🔌 Connecting to AI Clients

Use the SSE endpoint in your AI clients (Cursor, Claude Desktop, etc.):

- **SSE Endpoint**: `http://localhost:10880/sse`

---

## 🛠️ Local Development (Manual Setup)

If you prefer to run LogicHive without Docker:

```powershell
# 1. Install dependencies
uv pip install -e .

# 2. Start LogicHive MCP Server
uv run src/mcp_server.py
```

---

## 🛡️ Governance & License (SV-COS)

LogicHive is developed under the **Single-Vendor Open Source (SV-COS)** model.

- **Decision Power**: 100% of the strategic and technical roadmap is managed by **Ayato-Labs**.
- **Licensing**: Dual-licensed under **AGPL-3.0** and **Commercial**.
- **Contributions**: Requires [CLA Agreement](CLA.md).

---

## 💼 Commercial Licensing for LogicHive

LogicHive is dual-licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** and a **Commercial License**.

## Why a Commercial License?

The AGPL-3.0 is a strong copyleft license. If you use this software to provide a network service (SaaS), you are obligated to release your entire source code under the same license.

A Commercial License is required if you wish to:
1.  **Avoid AGPL-3.0 Obligations**: Use LogicHive as a part of a proprietary SaaS product or internal tool without disclosing your source code.
2.  **Embedded Use**: Integrate the logic hub into a closed-source commercial application.
3.  **Enterprise Support**: Receive guaranteed support, priority bug fixes, and custom feature development.

---

## License Tiers (Estimates)

| Tier | Target | Annual Fee | Features |
| :--- | :--- | :--- | :--- |
| **Indie** | Individuals / Revenue < $100k | $500 / year | Commercial use, No source disclosure |
| **Startup** | Startups < 50 employees | $2,000 / year | Tier 1 + Priority Email Support |
| **Enterprise** | Large Corporations / Custom needs | Contact us | Tier 2 + Custom SLA / On-premise support |

---

## Contact for Licensing

For inquiries regarding commercial licensing, custom deployments, or professional services, please contact Ayato-Labs:

- **Email**: [licensing@ayato-studio.ai](mailto:licensing@ayato-studio.ai)
- **Support via OFUSE**: [🛡️ Join the Community / Support via OFUSE](https://ofuse.me/21cfc1d2)

---
*Copyright (C) 2026 Ayato-Labs. All rights reserved.*

---

## 🇯🇵 日本語サマリー (Japanese Summary)

LogicHiveは、「仕様の再構築」や「冗長な実装」から開発者を解放するための**プロフェッショナル向けロジック・ハブ**です。

### 核心的な価値
- **死んだコードの撲滅**: 良質なロジックを「共有知」へ。
- **決定論的品質ゲート**: AIの温情を排し、AST解析(事実)が品質を担保する。
- **巨人の肩に乗る**: 書けば書くほど開発環境が強化される「知の資産化」。
- **デュアルライセンス**: OSSとしての普及と、商用利用での機密性保持を両立。

---

## 📄 License

Copyright (C) 2026 Ayato-Labs.  
Licensed under the [AGPL-3.0 License](LICENSE).
For commercial use, contact [Ayato Studio](https://ofuse.me/21cfc1d2).
