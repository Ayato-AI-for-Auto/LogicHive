# LogicHive Architecture Overview (Hybrid Edge-Cloud)

**最終更新日**: 2026-02-25
**バージョン**: 3.2.0

## 1. Product Vision

### 1.1 ビジョン
**LogicHive** は、**AIエージェントが生成したコードを「書き捨てない」ためのインフラ**である。
Cursor、Antigravity、Claude Desktop などのMCPクライアント環境から、プログラミング資産をシームレスに蓄積・再利用でき、毎回同じコードを生成し直すリソースの無駄を防ぐ。

### 1.2 The Hybrid Shift (Thin-Cloud 原則)
SaaSとしての体験を提供しつつ、運営コストを最小化するためのパラダイムシフト。

*   **Edge Storage**: 状態（ローカルDB/ベクトル検索）はEdge（ユーザーのPC環境）のDuckDBに持たせ、クラウドDB費用をゼロにする。
*   **Zero-Cost Global Storage**: パブリックな関数資産は GitHub リポジトリ (`LogicHive-Storage`) を『無料のグローバル共有DB』として利用する。ユーザーはここから MIT ライセンスの成果物を pull する。
*   **Cloud Intelligence**: 推論・品質評価・コード解析ロジックはGCP Cloud Run上のAPIに隠蔽。一番の「推論のノウハウ（IP）」は決して流出させない。
*   **Stateless Cloud**: バックエンドは状態を持たないため、安全にスケール・運用ができる。

### 1.3 設計方針（優先度）
1.  **IP（知的財産）の保護**: 知能ロジックをGCPエンドポイントの裏側に配置し、解析手法を秘匿する。
2.  **インフラコストの極小化**: 状態管理をEdgeに任せ、クラウド上のステートフルな費用を0にする。
3.  **クラウド・ネイティブとの融合**: 分散アーキテクチャによるスケーラビリティ。

### 1.4 デザインフィロソフィ
*   **Edge Compute Utilization**: ユーザーのローカルPCリソースを最大限活用する。
*   **Logic Obfuscation**: コード生成や選別ロジックをクラウドに置き、利用者に「知見」を物理的に渡すことなく機能を提供する。
*   **Draft First**: 高品質な関数の完成を待つよりも、下書き（Logic Draft）がそこにあることを優先する。品質はクラウド側の知能が評価・選別する。
*   **BYOK (Bring Your Own Key)**: ユーザーのAPIキーはクラウドに送信せず、常にローカルで推論を実行する。

---

## 2. アーキテクチャ全体構成 (Dual-Repo Architecture)
システムは、物理的に分離された2つのリポジトリによって独立稼働する協調アーキテクチャを採用している。
*   **Edge Client (`LogicHive-Edge` リポジトリ)**: ユーザーのローカルPCで状態を持つ、完全公開の OSS アプリケーション。
*   **Cloud Intelligence (`LogicHive-Hub-Private` リポジトリ)**: 運営側の知能（プロンプト・評価ロジック）を秘匿し、GCP上で完全自動デプロイされるプライベート SaaS バックエンド。

```mermaid
graph TD
    User[AI Agent / User] <-->|MCP Protocol (Stdio)| Proxies[TS MCP Proxy (Local Edge)]
    
    subgraph "User Local Environment (Edge)"
        Proxies <-->|Internal Call| PyAgent[Python MCP Tools]
        PyAgent <-->|Smart Cache Access| LocalDB[(Local DuckDB Cache)]
        Proxies -.->|File IO| ProjectDir[Project Directory]
    end

    subgraph "Global OSS Registry (Public)"
        PyAgent <-->|GitPython / MIT License| GitHubStorage[LogicHive-Storage Repo]
    end
    
    subgraph "GCP Cloud Run (Intelligence Hub / Secret Logic)"
        Proxies <-->|HTTPS REST API / Verify & Rerank| Master[FastAPI Background Server]
        
        subgraph "Stateless Logic Engine"
            Master --> Router[router.py (LLM Evaluation Prompt Gen)]
            Master --> QGate[quality_gate.py (Ruff/Security Check)]
        end
    end

    subgraph "External AI Services"
        Proxies -.-> |Direct HTTPS (BYOK)| Gemini[Google Gemini API]
    end
```

---

## 3. Monetization & Roadmap

LogicHive は、インフラコストを最小化しつつ持続可能なビジネスモデルを目指す。

### Phase 1: Free MVP (Current)
*   **モデル**: OSS 貢献型モデル
*   **ストレージ**: パブリック GitHub (`LogicHive-Storage`)
*   **ライセンス**: MIT ライセンス（登録した関数はグローバルに公開される）
*   **特徴**: GCPへのリクエスト上限があり。無料ユーザには一定数のリクエストを無料で提供する。また、GitHub リポジトリ (`LogicHive-Storage`) をすべての利用ユーザからpushしてもらうためのGCPを経由させる。

### Phase 2: Monthly Subscription (SaaS)
*   **モデル**: サブスクリプション制（月額制）
*   **特徴**: 専用プライベートDBの提供、リクエスト上限の拡張。ターゲットはプロフェッショナルな個人。

### Phase 3: Team & Enterprise Ops
*   **モデル**: 組織管理モデル
*   **特徴**: TeamIDによるアクセス制御、監査ログ、オンプレミスHubのデプロイ支援。
