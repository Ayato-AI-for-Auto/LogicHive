# LogicHive (Professional AI Logic Hub)

[![SafeSkill 89/100](https://img.shields.io/badge/SafeSkill-89%2F100_Passes%20with%20Notes-yellow)](https://safeskill.dev/scan/ayato-labs-logichive)
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

> [!IMPORTANT]
> LogicHive values **verifiability over correctness**. If an AI-generated logic atom lacks assertion tests, it is rejected by the Fact Gate, preventing low-quality code from polluting your knowledge base.

---

## 🌟 Key Features

- **Hybrid Knowledge Search**: Semantic and exact-match search for code patterns.
- **Verification Quality Gate**: Automated testing and linting before code is "vaulted".
- **MCP Streamable HTTP (SSE) Integration**: Centralized deployment serving multiple clients (Cursor, Claude Desktop) concurrently.
- **Project Isolation**: Manage logic assets across multiple namespaces and projects.

---

## 💼 Business Value & ROI

LogicHive turns transient AI interactions into reusable corporate assets:
1. **API Cost Optimization**: Drastically reduces LLM input tokens by injecting precise logic atoms instead of massive code context.
2. **Preventing Technical Debt**: Automatically blocks un-asserted, redundant, or complex code, slashing future maintenance costs.
3. **Secure AI Governance**: Filters out security vulnerabilities and runs isolated dynamic execution tests before storing assets.
4. **Capitalizing Organizational Knowledge**: Ensures critical domain logic is preserved and shared, eliminating project silo effects and key-person risks.

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

## ⚙️ Configuration

LogicHive is configured via environment variables or a `.env` file, resolving in the following order:

1.  **Local `.env` (Primary)**: Place `.env` in the same directory as `LogicHive-MCP.exe` (or project root).
2.  **User Home (Fallback)**: `~/.logichive/.env` (Global settings across folder moves).
3.  **OS Environment Variables**: Directly set variables override `.env` values.

**Setup Steps:**
1.  **Locate `.env.example`**: Copy this file to `.env`.
2.  **Set your API Keys**: At minimum, set `GEMINI_API_KEY`.
3.  **Place the file**: Follow the rules above based on your deployment.

See [.env.example](.env.example) and [ADR-005](docs/adr/005-configuration-resolution-strategy.md) for details.

---

### 🚀 自動起動の設定（タスクスケジューラー）

LogicHive を常駐させたい場合は、以下のコマンドを管理者権限の PowerShell で実行することでタスクスケジューラーに登録できます。

```powershell
# 設定例（パスは適宜調整してください）
$Action = New-ScheduledTaskAction -Execute "C:\Path\To\LogicHive-Hub.exe"
$Trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -Action $Action -Trigger $Trigger -TaskName "LogicHiveAutoStart"
```

---

## 🚀 Quick Setup & 120-Second Cursor Integration

To start using LogicHive immediately, follow these simple steps.

> [!TIP]
> **Demo Workflow in Action**  
> *(Insert Demo GIF showing LogicHive saving a verified Python function and suggesting it inside Cursor here)*

### Step 1: Run the LogicHive Server

LogicHive offers two friction-free distribution methods:

#### Option A: Windows Native EXE (Zero Friction & No Docker)
1. Download `LogicHive-Hub.exe` (Server) or `LogicHive-Settings.exe` (GUI) from the [Latest Release](https://github.com/ayato-labs/LogicHive/releases).
2. Run the `LogicHive-Hub.exe` via double-click or Command Prompt:
   ```cmd
   LogicHive-Hub.exe
   ```
3. The server runs natively on `http://localhost:10880/sse`.

#### Option B: OCI Container (Docker / Podman)
Run the pre-built image using standard container runtimes:
```bash
docker run -d \
  -p 10880:10880 \
  -e GEMINI_API_KEY=your_api_key_here \
  -v logichive_data:/app/storage/data \
  --name logichive-hub \
  ghcr.io/ayato-labs/logichive-hub:latest
```

---

### Step 2: Connect to AI Clients (MCP SSE)

Because LogicHive uses the **Streamable HTTP (SSE)** transport layer, setup is instant and does not require local script execution paths.

#### For Cursor
1. Navigate to **Settings > Features > MCP**.
2. Click **+ Add New MCP Server**.
3. Configure it as follows:
   * **Name**: `logichive`
   * **Type**: `SSE`
   * **URL**: `http://localhost:10880/sse`
4. Click **Save**.

#### For Claude Desktop
Add the following configuration block to your `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "logichive": {
      "url": "http://localhost:10880/sse"
    }
  }
}
```

#### For Generic `mcp.json`
```json
{
  "mcpServers": {
    "logichive": {
      "url": "http://localhost:10880/sse"
    }
  }
}
```

---

## 🛠️ Local Development (Manual Setup)

### Windows (Recommended)
We provide automated scripts for a seamless setup:

1.  **Run `dev_setup.bat`**: Creates a virtual environment and installs all dependencies in editable mode using `uv`.
2.  **Run `configure_logichive.bat`**: Opens the Settings UI to configure your LLM and Embedding providers.
3.  **Run `start_mcp_server.bat`**: Starts the LogicHive MCP server.

### Manual Commands
If you prefer manual control:

```powershell
# 1. Install dependencies
uv pip install -e .

# 2. Start LogicHive MCP Server
uv run src/mcp_server.py
```

---

## 🧪 Rigorous Testing & Deep Fact Verification

LogicHive employs a multi-layered, "Zero-Trust" testing architecture to ensure the reliability of both the hub and the assets it manages. Unlike standard test suites, we perform **Deep Fact Verification** by directly querying physical databases (SQLite/FAISS) to verify that data is correctly "vaulted" and retrieved.

### 1. Unit Tests (Atomic Verification)
- **Scope**: Individual functions and evaluators.
- **Goal**: Ensure logic gates (Deterministic, Security, AI) behave correctly at the AST and logic level.
- **Verification**: Tests invoke storage APIs and then use raw SQL to verify that the bits on the disk match the intended state.

### 2. Integration Tests (Feature Workflows)
- **Scope**: Orchestrator pipelines and background tasks.
- **Goal**: Validate that asynchronous verification flows, deduplication, and project isolation work seamlessly together.
- **Verification**: Simulates concurrent saves and checks that the background "Forensic Auditor" correctly promotes or rejects assets over time.

### 3. System Tests (User End-to-End)
- **Scope**: Full MCP tool calls and SSE transport layer.
- **Goal**: Ensure a user can search, save, retrieve, and delete logic through the Model Context Protocol without friction.
- **Verification**: Operates through the actual `mcp_server` interface, mimicking a real AI agent (like Cursor or Claude) using the service.

### 4. Chaos & Resilience (Negative Testing)
- **Scope**: Edge cases, performance limits, and intentional failures.
- **Goal**: Ensure the system handles "Evil Code" gracefully without crashing the hub.
- **Scenarios**:
  - **Infinite Loops**: Code that tries to hang the server is killed by hard timeouts.
  - **Database Locks**: Simulates high-contention or locked DB states to verify retry logic.
  - **Heavy Imports**: Rejects code that attempts to sneak in un-mocked massive libraries like `torch` or `tensorflow` during the static gate.

To run the suite:
```powershell
uv run pytest tests/unit tests/integration tests/system tests/chaos
```

---

## 🏢 Commercial & Enterprise Compliance (商用・ビジネス利用への対応)

LogicHiveは、ビジネス環境での商用利用およびエンタープライズ導入を前提として設計されています。
コア技術および依存関係には、商用利用に非常に寛容な **MIT** や **Apache 2.0** などのパーミッシブ・ライセンス（Permissive License）を採用しているライブラリのみを使用しており、法務的なコピーレフト汚染のリスクなく安心して導入いただけます。

### 依存技術のライセンス状況と根拠

LogicHiveを構成する主要な依存ライブラリと動作環境は以下の通りです。すべて商用利用可能なライセンスであることを確認済です。

| コンポーネント / ライブラリ | ライセンス | 根拠となるURL (LICENSE) |
| :--- | :--- | :--- |
| **Ollama (ソフトウェア本体)** | MIT | [GitHub](https://github.com/ollama/ollama/blob/main/LICENSE) |
| **Ollama Python Client** | MIT | [GitHub](https://github.com/ollama/ollama-python/blob/main/LICENSE) |
| **ChromaDB** | Apache 2.0 | [GitHub](https://github.com/chroma-core/chroma/blob/main/LICENSE) |
| **FastEmbed** | MIT | [GitHub](https://github.com/qdrant/fastembed/blob/main/LICENSE) |
| **FastMCP** | MIT | [GitHub](https://github.com/jlowin/fastmcp/blob/main/LICENSE) |
| **FastAPI** | MIT | [GitHub](https://github.com/tiangolo/fastapi/blob/master/LICENSE) |
| **Flet** | Apache 2.0 | [GitHub](https://github.com/flet-dev/flet/blob/main/LICENSE) |
| **Google GenAI** | Apache 2.0 | [GitHub](https://github.com/google-gemini/generative-ai-python/blob/main/LICENSE) |
| **Loguru** | MIT | [GitHub](https://github.com/Delgan/loguru/blob/master/LICENSE) |
| **HTTPX** | BSD 3-Clause | [GitHub](https://github.com/encode/httpx/blob/master/LICENSE.md) |
| **Pydantic** | MIT | [GitHub](https://github.com/pydantic/pydantic/blob/main/LICENSE) |
| **Stripe** | MIT | [GitHub](https://github.com/stripe/stripe-python/blob/master/LICENSE) |

> [!WARNING]
> **LLMモデルのライセンスについてのご注意**
> Ollamaソフトウェア自体はMITライセンスですが、Ollama上で実行する**各LLMモデル（Llama 3, Qwen, Gemmaなど）の商用利用条件はモデル提供者のライセンスに依存**します。商用利用の際は、自社のビジネス規模（MAUなど）が各モデルの商用利用許諾条件を満たしているか、ご自身で確認してモデルを選定してください。

> [!IMPORTANT]
> **セキュリティと機密性について**:
> LogicHiveのユーザーデータ（保存されたロジック資産等）は、ローカル環境のデータベース（SQLite/ChromaDB等）にのみ保持されます。AIプロバイダーへ送信されるのは、ユーザーが明示的にリクエストした範囲内のコンテキストのみであり、資産自体が外部へ漏洩する設計ではありません。

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
