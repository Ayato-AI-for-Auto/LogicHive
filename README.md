# LogicHive (formerly Function Store MCP)

**AIエージェントが生成したコードを「書き捨てない」ためのインフラストラクチャ**

現在のAIエージェント（Cursor, Claude Desktop, Antigravity 等）による開発には、大きな問題があります。
それは、**「AIが過去に書いたのと同じようなコードを、毎回ゼロから生成し直し、時間とコンピューティングリソースを無駄に消費している」** という点です。

LogicHive は、この「コードの書き捨て」を防ぐための MCP (Model Context Protocol) サーバーです。
エージェントが生成したプログラミング資産をシームレスに蓄積・検索・再利用し、AI開発における「記憶の連続性」と「資産化」を実現します。

> **設計思想**: **Local-First, Cloud-Verified**。検索や保存（下書き）はユーザーのローカル環境（DuckDB）で爆速・セキュアに行い、高度な品質検証や検索精度の向上（リランク）が必要な時だけ、クラウド上のAIロジック（GCP Cloud Run）を呼び出す「いいとこ取り」のハイブリッドアーキテクチャです。

## 主な特徴

- **AI Code Retention (資産の定着化)**: AIが生成した不完全な「コードの種」を即座にローカルへ保存（Draft-First）。プロジェクトをまたいで再利用可能な資産へと育て上げます。
- **Local-First & Zero Latency**: ベクトル検索エンジン（DuckDB/Qdrant Local）はユーザーのPC上で稼働するため、検索レイテンシはほぼゼロ。機密コードも意図的に共有するまでは完全にプライベートです。
- **Cloud-Verified Intelligence**: コードの品質検証、セキュリティチェック、セマンティック検索のリランクなど、重厚なAI処理はクラウド（GCP Cloud Run）にデプロイされたステートレスAPIが担当。ローカルリソースを枯渇させません。
- **Smart Get & Cognitive Logic**: `smart_search_and_get` ツールにより、AIエージェントが「自然言語での検索 -> 最適解の選別 -> プロジェクトへの自動配置」を1回の呼び出しで完結させます。
- **BYOK (Bring Your Own Key)**: ユーザー自身の Gemini API やローカルの Ollama を推論エンジンとして柔軟に選択可能です。

## 対象ユーザー

| ペルソナ | 利用シナリオ |
|---|---|
| **AIエージェント** | MCP経由で `smart_search_and_get` を自律実行し、車輪の再発明を回避 |
| **開発者 / ソフトウェアエンジニア** | Cursor等で過去のプロジェクトのロジックを瞬時に引き出し、開発速度を倍増 |
| **チーム / オープンソース** | クラウドのHubを共有し、チーム全体でAIプログラミングの知見（スニペット）を蓄積 |

---

## インストール方法 (Zero Friction)

本システムは **TypeScript プロキシ** を介して提供されるため、複雑なバックエンド環境の構築は意識させません。<br>
Node.js (v18+) がインストールされていれば、以下のコマンドだけでエディタに登録・使用可能です。

### 1. クラウドハブへ接続する場合（推奨：SaaSモード）

GCP Cloud Run などでホストされている LogicHive Hub に接続します。
詳細な手順は、[**SETUP_GUIDE.md**](./SETUP_GUIDE.md) をご覧ください。

Cursor の場合：
- **Name**: `LogicHive`
- **Type**: `command`
- **Command**: `npx -y @ayato-ai/function-store-mcp@latest --hub-url https://api.hive.ayato-studio.ai`

### 2. 自分専用のクラウドハブを構築する場合 (BYOK)

提供されている自動デプロイツールを使って、ご自身の GCP プロジェクトに数分でデプロイできます。

```powershell
# GCPにログイン
gcloud auth login

# デプロイ (ご自身のプロジェクトIDとGemini APIキーを指定)
python dev_tools/deploy.py --project <YOUR_PROJECT_ID> --gemini-key <YOUR_GEMINI_KEY>
```
デプロイ後に出力されるURLを、上記のエディタ設定(`--hub-url`)に使用してください。

---

## プロバイダー設定 (Gemini vs Ollama)

バックエンド（Hub）起動時またはデプロイ時の環境変数で、推論エンジンを切り替えられます。

- **Gemini (Default Cloud)**
  - `FS_MODEL_TYPE=gemini`
  - `FS_GEMINI_API_KEY=your_key`
- **Ollama (Self-Hosted / Local)**
  - `FS_MODEL_TYPE=ollama`
  - `FS_OLLAMA_BASE_URL=http://localhost:11434`
  - `FS_OLLAMA_EMBED_MODEL=mxbai-embed-large`
  - `FS_OLLAMA_CHAT_MODEL=qwen2.5-coder:7b`

---

## 利用可能な MCP Tools

登録後、AIエージェントから以下のツールが利用できます：

| Tool | 分類 | 説明 |
|---|---|---|
| `smart_search_and_get` | **メイン** | 自然言語で検索 -> 最適解の選別 -> プロジェクトへ自動配置を1発で実行 |
| `search_functions` | 探索用 | 既存の資産をセマンティック検索してブラウズ |
| `save_function` | 保存用 | 関数を保存（「下書き」保存対応。自動品質・セキュリティチェック付） |
| `get_function` | 取得用 | 関数のソースコード（依存関係の統合バンドル可）を取得 |
| `inject_local_package` | 配置用 | 指定した名前の関数を `local_pkg/` に物理エクスポート |
| `get_triage_list` | 診断用 | 修正の必要な下書きや低品質な関数をリストアップ |

-   **`smart_search_and_get(query, target_dir)`**: **推奨される唯一の入り口**。AIエージェントが「〜をするロジックが欲しい」と伝えるだけで、全ての工程を自動化します。
-   **`save_function(...)`**: 構文が不完全でも「下書き」として保存可能。説明文が空でもAIが補完します。

## ベストプラクティス：AIとの協働（Draft First）

本システムは、**「AIエージェントが生成した未完成の種を、いかに速く資産に変えるか」**、そして**「それをいかに楽に再利用するか」**に特化しています。

- **Draft First (下書き保存)**: 
    - 保存時に完璧なコードである必要はありません。構文エラーがあっても保存し、後で `smart_search_and_get` で呼び出した後に Cursor 等で修正する方が効率的です。
- **Smart Module Support**: 
    - 関数間の依存関係（同一プロジェクト内の別関数呼び出し）は自動で解決されます。`get_function` もしくは `smart_search_and_get` を使えば、必要な依存コードは全て統合された状態で提供されます。
- **外部ライブラリの明示**: 
    - `pip` でインストールが必要な外部ライブラリは `dependencies` に含めてください。導入時に自動検証・環境隔離が行われます。

---

## プロジェクト構造

```text
.
├── ts-proxy/              # TypeScript MCP Proxy (npm package)
├── backend/mcp_core/      # コアロジック (LogicHive Engine)
├── dev_tools/             # CI/CD および デプロイツール (`deploy.py`)
├── docs/                  # 設計書等
├── Dockerfile             # Cloud Run デプロイ用軽量コンテナ
└── pyproject.toml         # Python 依存関係 (uv)
```

## 開発者向け

```powershell
uv run python dev_tools/dev.py              # Lint + Test 一括実行
uv run python dev_tools/dev.py --ship -m "msg" # CI + Git Push
```

---

Created by Ayato AI & LogicHive Architect.
