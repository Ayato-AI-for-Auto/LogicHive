# ADR-0017: Embeddingモデルごとのベクターストア分離と自動再構築戦略

- **Date**: 2026-06-06
- **Status**: Superseded by [ADR-0018](./ADR-0018-thin-client-dynamic-venv.md)
- **Deciders**: ayato-labs (ユーザー), Gemini CLI

## Context
LogicHive はローカル（Ollama/FastEmbed）とクラウド（Gemini）のハイブリッド構成を採用しており、ユーザーは Settings UI から自由に LLM および Embedding モデルを切り替えることができる。
しかし、現在の設計ではベクトル検索用のインデックスファイルパス (`FAISS_INDEX_PATH`) が `faiss_index.bin` として静的に固定されている。

異なる Embedding モデルは、出力されるベクトルの次元数（Dimension）が異なるだけでなく、意味空間（セマンティクス）も完全に異なる。
そのため、以下の重大な問題が発生する：
1. **Dimension Mismatch**: 次元の異なるモデルに切り替えた際、既存の Faiss インデックスの次元と合致せず、サーバーがクラッシュする。
2. **Semantic Corruption**: 次元の同じ別モデルに切り替えた場合、クラッシュはしないものの、クエリベクトルと保存済みベクトルの意味空間がズレるため、検索精度が完全に崩壊する。

## Decision
この課題を解決し、RAG（Retrieval-Augmented Generation）システムとしての健全性を保つため、以下のアーキテクチャ方針を採用する。

### 1. インデックスの物理的分離 (Model-Specific Isolation)
- `FAISS_INDEX_PATH` を静的なファイル名ではなく、現在の `EMBEDDING_MODEL_ID` から安全な文字列（サニタイズされたモデル名）を動的に生成し、ファイル名に含める（例: `faiss_gemini-embedding-2.bin`）。
- これにより、モデルを元のものに戻した場合、過去に構築したインデックスを再利用（キャッシュとして機能）できる。

### 2. 真のデータソース (Source of Truth) の維持と自動再構築
- ベクトルインデックスはあくまで「検索用のキャッシュ」として扱い、真のデータ（Source of Truth）は一元化された SQLite データベース（`logichive.db`）の履歴として維持する。
- LogicHive サーバーの起動時、またはベクトルストアの初期化時に、指定されたモデルの Faiss インデックスファイルが存在しない（空である）場合、SQLite データベースに保存されている過去のナレッジを全件読み出し、自動的にバックグラウンドでエンベディングを再計算してインデックスを構築（マイグレーション）するロジックを実装する。

### 3. UIによるライフサイクル管理 (Cache Management)
- 古いモデルのインデックスファイルは徐々にストレージを圧迫する可能性があるため、Settings UI に以下の機能を提供する。
  - **Rebuild Vector Index**: 現在のモデルでインデックスを強制的にゼロから再構築する機能。
  - **Clear Vector Cache**: 選択されていない過去のモデルのインデックス、またはすべてのベクトルインデックスを削除（パージ）する機能。

## Consequences
### Positive
- モデル切り替え時の Dimension Mismatch エラーや検索精度の崩壊を完全に防ぐことができる。
- SQLite を Source of Truth とすることで、いつでもどのモデルでも過去のデータをベクトル空間に復元できる（耐障害性の向上）。
- 過去に使ったモデルに戻した際、再計算のコストを払うことなく即座に稼働できる。

### Negative / Risks
- **ストレージ消費の増加**: モデルごとにインデックスが生成されるため、複数モデルを頻繁に切り替えるとストレージ消費が増える。UI 側での手動パージ機能によるフォローが必要。
- **初回切り替え時のレイテンシ**: インデックスの自動再構築（マイグレーション）時、保存されているデータ量が多い場合は API 制限（Rate Limit）や再計算に時間がかかる可能性がある。UI やログで進行状況を適切に通知する工夫が求められる。

## References
- ADR-0012: Centralized User Data Storage
- ADR-0014: Standardized Hybrid Configuration Strategy
- ADR-0031: Embedding Resilience and Recovery Strategy (後継の救済策)

## Amendment: FAISS レガシーコードクリーンアップ完了 (2026-07-05)

### Context
ADR-0017 で策定された FAISS インデックス分離戦略は、ADR-0018 の ChromaDB 移行により実質的に解決済みであったが、コードベースに FAISS 残骸が残存していた。

### Completed Cleanup
1. `src/mcp_server.py:467` — docstring の "FAISS vector index" → "ChromaDB vector index" に修正
2. `src/core/logging_config.py:142` — FAISS ログ抑制リストから `"faiss"` を削除
3. `.gitignore` — `src/storage/data/` と `* (1)*` パターンを追加
4. Phase 1 クリーンアップ完了 — 25件の重複ファイル、11件の `__pycache__` ディレクトリ、`logichive_hub.egg-info/` を削除

### Status
FAISS 関連のコード参照は完全に排除され、ADR-0017 は **Superseded + Resolved** となった。
