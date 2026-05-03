# LogicHive (Professional AI Logic Hub)

🛡️ **LogicHive** is a high-precision knowledge extraction and logic management system. It enables AI agents to accumulate, verify, and reuse high-quality code assets via the Model Context Protocol (MCP).

> **"Stop rebuilding the same logic. Build a long-term intelligence asset."**  
> **哲学:巨人の肩の上に乗り、真に価値ある創造に集中せよ。**

## 🌟 Key Features

- **Hybrid Knowledge Search**: Semantic and exact-match search for code patterns.
- **Verification Quality Gate**: Automated testing and linting before code is "vaulted".
- **MCP Integration**: Seamlessly expose complex logic to AI agents.
- **Project Isolation**: Manage logic assets across multiple namespaces and projects.

---

## 🏗️ Architecture

For a deep dive into the design decisions and system structure, please refer to:
[**ARCHITECTURE.md**](ARCHITECTURE.md)

---

## 🛡️ Governance & License (SV-COS)

LogicHive is developed under the **Single-Vendor Open Source (SV-COS)** model.

- **Decision Power**: 100% of the strategic and technical roadmap is managed by **Ayato Studio**.
- **Licensing**: This project is dual-licensed:
    - **Open Source**: [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE)
    - **Commercial**: For SaaS, embedded use, or enterprise support, see [**COMMERCIAL.md**](COMMERCIAL.md).
- **Contributions**: We welcome contributions! However, all contributors must agree to our [**Contributor License Agreement (CLA)**](CLA.md) to ensure the project's sustainability.

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

```python
def perform_clustering(data):
    from sklearn.cluster import KMeans  # Lazy Import
    model = KMeans(n_clusters=3)
    return model.fit_predict(data)
```

### 2. Smart Mocking
If you must have top-level imports, use the `mock_imports` parameter in `save_function`. LogicHive will inject `MagicMock` for those modules during verification, allowing the logic structure to be validated without loading the actual library weight.

```python
# LogicHive will mock 'torch' if provided in mock_imports list
import torch

def get_device():
    return "cuda" if torch.cuda.is_available() else "cpu"
```

---

## 🚀 Quick Setup

```powershell
# 1. Install dependencies
uv pip install -e .

# 2. Register MCP Server
uv run src/mcp_server.py
```

---

## 🇯🇵 日本語サマリー (Japanese Summary)

LogicHiveは、「仕様の再構築」や「冗長な実装」から開発者を解放するための**プロフェッショナル向けプライベート・ロジック・ハブ**です。

### 核心的な価値
- **死んだコードの撲滅**: 良質なロジックを「共有知」へ。
- **決定論的品質ゲート**: AIの温情を排し、AST解析(事実)が品質を担保する。
- **巨人の肩に乗る**: 書けば書くほど自分の開発環境が強化される「知の資産化」。

---

## 📄 License

Copyright (C) 2026 Ayato-Labs.  
Licensed under the [AGPL-3.0 License](LICENSE).
For commercial use, contact [Ayato Studio](https://ofuse.me/21cfc1d2).
