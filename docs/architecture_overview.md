# LogicHive Architecture Overview (Hybrid Edge-Cloud)

**最終更新日**: 2026-02-25
**バージョン**: 3.2.0

## 1. Product Vision

### 1.1 ビジョン
**LogicHive** は、**AIエージェントが生成したコードを「書き捨てない」ためのインフラ**である。
Cursor、Antigravity、Claude Desktop などのMCPクライアント環境から、プログラミング資産をシームレスに蓄積・再利用でき、毎回同じコードを生成し直すリソースの無駄を防ぐ。

また、知財（IP）の保護とセキュリティの観点から、アーキテクチャを「エージェント側のローカル環境（Edge）」と「処理と記憶を司るクラウド環境（Hub）」に分離した。これにより、ユーザーの環境からAPIキーを流出させることなく、高度な推論とセマンティック検索を提供する。

### 1.2 The Hybrid Shift (Thin-Cloud 原則)
SaaSとしての体験を提供しつつ、運営コストを最小化するためのパラダイムシフト。

*   **Edge Compute & Cache**: ローカル環境（Edge）のDuckDBは一時的なキャッシュとプロジェクト固有の状態管理に留め、重い処理をクラウドへオフロードする。
*   **Intelligence-Driven Global Storage (Supabase)**: 世界中の関数資産は Supabase (PostgreSQL + pgvector) を『インテリジェンス・バンク』として一元管理する。**768次元**のベクトル検索（`gemini-embedding-001`）により、ユーザーは自然言語から最適なコードを即座に取得できる。
*   **Cloud Intelligence & Security**: 推論・品質評価・コード解析ロジックはGCP Cloud Run上のHubで完結。**AST解析によるセキュリティ検証**と**検索精度の最適化**を主軸とする。
*   **Stateless Cloud Engine**: バックエンドは永続化を Supabase に委譲し、自身はステートレスな推論エンジンとして高速に稼働する。

### 1.3 設計方針（優先度）
1.  **UXファースト (No BYOK)**: ユーザーにAPIキー設定を強引に求めず、運営側のインフラで即座に価値を提供する。
2.  **IP（知的財産）の保護**: 知能ロジックと推論指示（プロンプト）をGCPエンドポイントの裏側に配置し、解析手法を秘匿する。
3.  **インフラコストの極小化**: 状態管理（DB）をEdgeに任せ、クラウド上のステートフルな費用を0にする。

### 1.4 デザインフィロソフィ
*   **Edge Compute Utilization**: ユーザーのローカルPCリソースを最大限活用する。
*   **Direct Intelligence**: 複雑な往復通信を廃止し、クラウド側で推論を完結させてレスポンス速度を向上させる。
*   **Draft First**: 高品質な関数の完成を待つよりも、下書き（Logic Draft）がそこにあることを優先する。品質はクラウド側の知能が評価・選別する。
*   **MIT License Agreement**: 無料利用の対価として、登録コードへのMITライセンス付与に同意してもらう。
### 1.5 Security & Defense (Scraping Guard)
MVPフェーズにおける利便性（APIキー不要）と資産保護を両立するため、**「Search -> Mask -> Get」**の多層防御フローを採用。
*   **Data Masking**: 検索結果からはソースコードを完全に除去し、メタデータのみを返却。
*   **Per-IP Rate Limiting**: 検索およびコード取得の頻度をIP単位で極小化し、プログラムによる全件抽出を阻止する。

---

## 2. アーキテクチャ全体構成 (Dual-Repo Architecture)
システムは、物理的に分離された2つのリポジトリによって独立稼働する。
*   **Edge Client (`LogicHive-Edge`)**: ユーザーのローカルPCで動作する直接型 Python MCP サーバー。
*   **Cloud Intelligence (`LogicHive-Hub-Private`)**: 運営側の知能（プロンプト等）を秘匿し、GCP上で動作するプライベート SaaS バックエンド。

```mermaid
graph TD
    User[AI Agent / User] <-->|MCP Protocol (Stdio)| PyAgent[LogicHive Edge (Python MCP)]
    
    subgraph "User Local Environment (Edge)"
        PyAgent <-->|Smart Cache Access| LocalDB[(Local DuckDB Cache)]
        PyAgent -.->|File IO| ProjectDir[Project Directory]
    end

    subgraph "GCP Cloud Run (Intelligence Hub)"
        PyAgent <-->|HTTPS REST API / Search & Get| Master[FastAPI Background Server]
        
        subgraph "Security & Intelligence"
            Master --> Guard[Rate Limiter & Masking]
            Master --> Router[router.py (Rerank)]
        end
    end

    subgraph "Core Cloud Storage"
        Master <--> |pgvector Search/Upsert| Supabase[(Supabase Vector DB)]
    end

    subgraph "External AI Services"
        Router -.-> |Direct HTTPS| Gemini[Google AI (Gemma 3)]
    end
```

---

## 3. Monetization & Roadmap

LogicHive は、インフラコストを最小化しつつ持続可能なビジネスモデルを目指す。

### Phase 1: Intelligent MVP (Current)
*   **モデル**: OSS 貢献型モデル
*   **ストレージ**: Supabase Vector DB (Free Tier活用)
*   **ライセンス**: MIT ライセンス（登録した関数はグローバルに公開される）

### Phase 2: Team & Enterprise Ops
*   **モデル**: 組織管理モデル
*   **特徴**: TeamIDによるアクセス制御、監査ログ、オンプレミスHubのデプロイ支援。
