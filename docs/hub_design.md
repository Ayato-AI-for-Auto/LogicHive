# Hub Design (Cloud Intelligence Architecture)

このドキュメントは、GCP Cloud Run上で動作する **Hub** コンポーネント（Cloud Intelligence Hub）の詳細設計を記述する。

## 1. 責務とコア概念

Hub層の主な責務は以下の通り：
1.  **プロファイリングと知能の提供**: 検索時のリランキングやコードの品質評価、セキュリティ検証を直接実行する。
2.  **IP（知的財産）の秘匿**: 「高品質な評価プロンプト」や「検索最適化ロジック」をクラウド側に閉じ込め、リバースエンジニアリングから保護する。
3.  **効率的な永続化**: Supabase (pgvector) を活用し、ステートレスな推論エンジンとして軽量に保つ。
4.  **セキュリティ・ガード**: AST 静的解析により、秘密情報（APIキー等）や危険な呼び出しを含むコードの登録を拒否する。
5.  **スクレイピング防衛 (Defense in Depth)**: レート制限とデータ隠蔽により、バルクダウンロードを物理的に低速化・困難にする。
6.  **知能のクレンジングとランク付**: 保存時の自動タグ付けと、利用実績に基づく動的な検索順位調整を行う。

## 2. コンポーネント詳細

### 2.1 FastAPI Server (`backend/hub/app.py`)
*   **ホスティング**: GCP Cloud Run (Serverless)。アクセスがない時はインスタンスをゼロにでき、運用コストを最適化。
*   **レート制限**: メモリベースの `RateLimiter` を搭載。同一IPからの過剰な操作（検索:10回/分, コード取得:5回/分）を遮断する。

### 2.2 Intelligence Router (`backend/hub/router.py`)
ユーザーのクエリに対し、最適な関数を選別して返す。

*   **Popularity-biased Reranking**: 
    1. ベクトル類似度による上位候補の抽出。
    2. **Weighted Scoring**: `Similarity + 0.1 * log10(call_count + 1)` により、実績のある関数を上位にブースト。
    3. 上位結果からコードを秘匿（Mask）した状態で返却。

### 2.3 Quality Gate & Security (`backend/core/quality.py` / `security.py`)
*   **Security**: `ASTSecurityChecker` による危険な関数呼び出しの検知。

### 2.4 Intelligent Indexing (`backend/hub/consolidation.py`)
ユーザーからアップロードされた「雑な」情報を、AI（Gemma 3）が補完・強化する。
*   **Metadata Optimization**: コードを解析し、プロフェッショナルな説明文と検索タグを自動生成して保存。これにより、検索精度をシステム側で担保する。

### 2.5 Scraping Defense (`backend/hub/app.py`)
MVPフェーズにおける「APIキーなし」の利便性とセキュリティを両立させるため、以下の仕組みを採用する。
*   **検索結果のマスキング**: 検索リプライから `code` フィールドを削除。
*   **2フェーズ取得 (Search -> Get)**: 具体的な関数名が判明した後に個別にコードを取得するフローを強制し、摩擦（Friction）を生じさせる。

## 3. なぜ「知能集権化」へ舵を切ったのか？

1.  **UXの最適化**: ユーザー側のAPIキー不要（No Auth / No BYOK）。
2.  **知能の自己洗練**: 保存されたコードがAIによって自動的にタグ付けされ、利用されるほど順位が上がる「生きている知能バンク」への進化。
3.  **防衛能力の向上**: クラウド側での一元的なトラフィック制御。

## 4. Dual-Repo Architecture

Hubはプライベートリポジトリ（`LogicHive-Hub-Private`）で管理され、評価プロンプトやセキュリティルール、順位調整アルゴリズム（ブースト値等）を秘匿する。

## 5. デプロイメント・フットプリント

### ✅ GCP上（Cloud Run向け）に必要なファイル
*   `backend/hub/` : FastAPIサーバー、知能ロジック。
*   `backend/core/` : 共有設定、セキュリティロジック。
*   `google-genai` : クラウド側での推論（Embedding, Rerank, Auto-index）に必須。

### 🗑️ コンテナから除外すべきファイル
Hubの役割（司令塔・ルーター）に無関係なものをコンテナに含めると、イメージサイズが肥大化し（コールドスタートの遅延やコスト増）、セキュリティのアタックサーフェスも広がります。
*   `duckdb`, `gitpython` : Hubはローカルファイル操作を必要としない。
*   **開発用ツール**: 本番Runtimeには不要なテストコード。
