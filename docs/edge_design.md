# Edge Design (Local Client Architecture)

このドキュメントは、ユーザーのローカルPC環境で動作する **Edge** コンポーネントの詳細設計を記述する。

## 1. 責務とコア概念

Edge層の主な責務は以下の通り：
1.  **AI エージェントとのインターフェース**: MCPプロトコルを介して Cursor などのエディタと通信する。
2.  **ステートフルなデータ管理**: ユーザーのPCのストレージを利用し、DuckDBを用いたローカルキャッシュとベクトル検索を実行する。
3.  **OSSストレージとの同期**: GitHub上にホストされた関数リポジトリ（`LogicHive-Storage`）との同期を担当する。
4.  **安全なモデル実行 (BYOK)**: ユーザー自身のAPIキーを用いて、ローカルから直接LLMへ推論リクエストを送る（Hubへはキーを送らない）。

## 2. コンポーネント詳細

### 2.1 Thin Proxy (`ts-proxy/src/index.ts`)
TypeScriptで書かれたMCPサーバー。
*   **役割**: エディタに登録される主要なエントリーポイント。
*   **Thin（薄い）設計**: 以前はDB操作を直接行っていたが、現在はDBロック競合を防ぐため、すべてのデータ永続化とビジネスロジックをPythonベースの バックエンド (`backend/edge/mcp_server.py`) へCLI経由で委譲している。
*   **Hubとの調整役**: ローカル(Python)で関数をPending状態で保存した後、GCP Hubに対して「評価用プロンプト」を要求し、ローカルでLLMを実行して、結果をHubに返す「Reverse Intelligence フロー」を統括する。

### 2.2 Local Intelligence & Data (`backend/edge/mcp_server.py`)
Pythonで書かれた裏側のローカル処理の核。
*   **役割**: DuckDBの単一オーナー。ベクトル検索、関数の永続化、メタデータの管理を行う。
*   **FastMCP**: 将来的には `ts-proxy` を介さず、Python環境単独でもMCPサーバーとして起動できるように口が用意されている。

### 2.3 GitHub Sync Engine (`backend/edge/sync.py`)
*   **役割**: グローバルな関数資産（`LogicHive-Storage`）とローカルのDuckDBキャッシュとの同期を行う。
*   **実装**: `GitPython` ライブラリを使用しており、バックグラウンドで `git pull` や `git push` を発行し、JSON形式のファイル群をDBへUpsertする。

## 3. Reverse Intelligence Flow (Edge側の視点)

ハイブリッドな検索と取得（`smart_search_and_get`）を行う際のシーケンス：

1.  **Local Broad Search**: `ts-proxy` はローカルのDuckDBに対してあいまいなベクトル検索を実行し、候補（Candidates）を取得する。
2.  **Prompt Request**: Cloud Hub に対して「候補群の中からユーザーのクエリに最適なものを選ぶためのプロンプト」を要求する。
3.  **Local Execution**: Hub から返ってきたプロンプト（=運営の隠匿されたノウハウ）を、ユーザーのAPIキーを使ってローカルからLLMへ投げる。
4.  **Finalize & Inject**: LLMの選別結果をHubに報告し（ここでHubが必要ならログを取る）、Edge側で選ばれた関数のコードを実際のプロジェクトの `local_pkg/` にファイル出力する。

## 4. データモデル (DuckDB Schema)

`functions` テーブルを中心に構成される。

*   `id`: INTEGER (Primary Key)
*   `name`: VARCHAR (Unique Function Name)
*   `code`: VARCHAR (Source Code)
*   `description`: VARCHAR
*   `tags`: VARCHAR (JSON String)
*   `metadata`: VARCHAR (JSON String, including quality score, dependencies)
*   `status`: VARCHAR ('pending', 'verified', 'broken', 'archived')
*   `test_cases`: VARCHAR (JSON String)

※埋め込み(Embeddings)の次元数は、Edge側で使用するモデルによって動的に格納される。
