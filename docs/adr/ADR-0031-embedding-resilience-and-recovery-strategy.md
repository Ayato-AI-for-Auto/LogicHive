# ADR-0031: Embedding Resilience and Recovery Strategy

- **Date**: 2026-07-05
- **Status**: Accepted
- **Deciders**: ayato-labs (User), opencode/mimo-v2.5-free (Agent)

## Context

LogicHive のナレッジベースは、ユーザーが関数を保存するたびに以下の一連のフローを経て RAG 検索可能なインデックス構築を行う：

1. `orchestrator.do_save_async()` が実行される
2. `storage.save_function()` で DB に保存（ステータス `draft`）
3. `orchestrator.verify_asset_async()` がバックグラウンドで起動
4. 検証ゲート（判定、ランタイム、静的解析、AIゲート）が通過すると `status=verified` に更新
5. ベクトル埋め込み（Embedding）が生成され、DB と ChromaDB ベクトルストアに同期される

しかし、2026年7月5日の本番環境検証で、以下が判明した：

### 根本原因
- **初期起動時の APIキー欠如**: サーバー初回起動時に `GEMINI_API_KEY` が未設定だった。
- **サイレント失敗**: `core/embedding.py` は API キーが無効な場合、例外をスローせず、`[0.0] * VECTOR_DIMENSION`（ゼロベクトル）を返却していた。
- **埋め込みスキップ**: `orchestrator.py` は `embedding` が空ベクトルの場合、DB の `update_function_embedding()` をスキップし、ChromaDB への同期も行われなかった。
- **結果**: 98件中93件が DB に保存済みだが、埋め込みが `None` または `[]` のまま。ベクトルストアには5件のみ登録。

### 課題
1. **救済手段の欠如**: 埋め込みがスキップされた関数を後から一括復旧する手段が存在しなかった。
2. **サイレント失敗**: API エラーやネットワーク障害時、ユーザーに通知されず静かに失敗する。
3. **再発リスク**: API キー切れ、レート制限、一時的ネットワーク障害で再発する可能性がある。

## Decision

### 1. 埋め込み生成失敗時の例外化 (`embedding.py`)
- API キー無効時、プロバイダ接続失敗時、レート制限時に `EmbeddingUnavailableError` をスローする。
- ゼロベクトル返却は廃止する。
- 例外クラスは `core/exceptions.py` に定義し、全プロバイダ（Gemini、Ollama、FastEmbed）で共通使用する。

### 2. 検証フローでの埋め込み失敗時の状態遷移 (`orchestrator.py`)
- `generate_embedding()` が `EmbeddingUnavailableError` をスローした場合：
  - DB の `verification_status` を `embedding_pending` に設定する。
  - リトライキューに積む（メモリ上キュー）。
  - ベクトルストアへの同期は行わない。
- リトライは指数バックオフ（最大3回、10秒/30秒/60秒）で実行する。

### 3. `rebuild_embeddings` MCP ツールの新設
- 既存 `rebuild_index` は「DB の埋め込みからベクトルストアを再構築」するのみで、埋め込みの未生成問題は解決しない。
- 新ツール `rebuild_embeddings` は以下のフローで全件復旧する：
  1. `embedding IS NULL` または `embedding = '[]'` の関数を DB から取得
  2. 各関数について、`metadata` を再構築し、`generate_embedding()` を実行
  3. 成功時は DB の `update_function_embedding()` と ChromaDB への同期を実行
  4. 失敗時はスキップし、次の関数に進む
  5. 進行状況をログに出力し、完了時にサマリー（成功/失敗/スキップ件数）を返却
- API レート制限対策として `asyncio.Semaphore(3)` で同時実行数を制限する。

### 4. 起動時の自動整合性チェック (`mcp_server.py`)
- サーバー起動時に `validate_config_lazy()` の結果を確認
- API キーが有効な場合、`embedding IS NULL` の関数件数をチェック
- 件数 > 0 なら警告ログを出力し、自動で `rebuild_embeddings` を実行するオプションを提供

## Consequences

### Positive
- **93件の埋め込み復旧**: `rebuild_embeddings` の実行で既存データを完全復旧できる。
- **再発防止**: API エラー時にサイレント失敗が起きなくなり、適切に状態が管理される。
- **運用視認性**: 起動時の整合性チェックにより、問題の早期検知が可能になる。

### Negative / Risks
- **リトライのオーバーヘッド**: 指数バックオフでリトライするため、大量の関数で一時的な API 負荷が増加する可能性がある。`Semaphore(3)` で軽減。
- **`embedding_pending` 状態の管理**: リトライキューが破損した場合（プロセスクラッシュ）、`embedding_pending` 状態の関数が残るリスク。起動時の自動チェックでカバー。

## References
- Issue: Embedding sync failure (98 DB records, only 5 embedded)
- Root cause log: `~/.logichive/logs/hub.1.jsonl` — `CONFIGURATION INCOMPLETE: GEMINI_API_KEY is missing`
- ADR-0017: Embedding Model Isolation (Superseded)
- ADR-0018: Thin Client + Dynamic Venv Architecture

## Amendment: FAISS Legacy Cleanup Completion (2026-07-05)

### Context
ADR-0017 で策定された FAISS インデックス分離戦略は、ADR-0018 の ChromaDB 移行により実質的に解決済みであったが、コードベースに FAISS 残骸が残存していた。

### Completed Cleanup
1. `src/mcp_server.py:467` — docstring の "FAISS vector index" → "ChromaDB vector index" に修正
2. `src/core/logging_config.py:142` — FAISS ログ抑制リストから `"faiss"` を削除
3. `.gitignore` — `src/storage/data/` と `* (1)*` パターンを追加
4. Phase 1 クリーンアップ完了 — 25件の重複ファイル、11件の `__pycache__` ディレクトリ、`logichive_hub.egg-info/` を削除
