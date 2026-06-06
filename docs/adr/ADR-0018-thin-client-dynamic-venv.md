# ADR-0018: Thin Settings Client and Dynamic Hub Engine Venv

- **Date**: 2026-06-06
- **Status**: Accepted
- **Deciders**: ayato-labs (ユーザー), Gemini CLI

## Context
LogicHive の配布戦略として、ADR-002 では「完全なスタンドアロン EXE (PyInstaller)」による配布を採用していた。
しかし、開発が進むにつれ、以下のような深刻な課題（技術的負債）が浮き彫りになった：
1. **外部依存の制限**: ChromaDB などのネイティブ依存が強い最新の C++/Rust 系 AI ライブラリを導入しようとすると、PyInstaller のビルドが失敗し、EXE サイズが数百MB〜GBクラスに肥大化する。
2. **車輪の再発明**: EXE 化の制約（依存ライブラリを増やせない）により、Faiss と SQLite を手動で同期するような複雑でバグを生みやすい RAG ロジックを自作（車輪の再発明）せざるを得なくなっていた。
3. **アップデートのコスト**: 数行のバグ修正でも巨大な EXE の再ビルドと再配布が必要となり、運用・維持管理コストが増大していた。

## Decision
開発コスト、維持管理コスト、そして将来の拡張性（継続開発）を最優先するため、ADR-002 の「完全 EXE 化」を破棄し、以下の **「Thin Client + Dynamic Engine」** アーキテクチャへとパラダイムシフトする。

1. **Thin Settings Client (EXE)**:
   - ユーザーが直接触れる `LogicHive-Settings` のみ、軽量な EXE（Flet ベース）としてコンパイルして配布する。
   - これにより「ダブルクリックで起動する」という最高の UX（Zero Friction）を維持する。

2. **Dynamic Hub Engine Venv**:
   - Settings EXE が初回起動された際、内部で自動的に `uv` を使用し、ユーザー環境の `~/.logichive/.venv` に Python 仮想環境を動的構築する。
   - Hub エンジン（RAG、ベクトル検索、MCP機能など）はこの専用 venv 内で実行される。

3. **依存関係の解放**:
   - エンジンが通常の venv で動くため、ChromaDB や Qdrant、LangChain といった業界標準のライブラリを制約なく導入可能とする。泥臭い自前実装（Faissの同期ロジック等）は廃止し、これら外部ライブラリのエコシステムに乗る。

## Consequences
### Positive
- **技術的負債の劇的削減**: ベクトルデータベースの同期や管理など、専門性の高い機能を業界標準ライブラリに丸投げできる。
- **配布サイズの極小化**: EXE は軽量な UI のみとなり、ダウンロードが一瞬で終わる。
- **高速なアップデート**: エンジンの更新は `uv pip install --upgrade` などを裏で走らせるだけで完結し、巨大なバイナリの入れ替えが不要になる。

### Negative / Risks
- **誤検知リスク (False Positives)**: EXE が裏で別プロセス（`uv`）を呼び出して環境を構築する振る舞いは、セキュリティソフト（Windows Defender 等）からドロッパーと誤検知されるリスクがある。ドキュメントでの注意喚起や、将来的なコードサイニング証明書の取得で対応する。
- **初回起動時のネットワーク依存**: 初回のみ、ライブラリ群のダウンロードにインターネット接続と若干の時間が必要になる。

## References
- ADR-002: Dual Distribution Strategy (Superseded by this ADR)
- ADR-015: Lightweight Ephemeral Environments
- ADR-017: Embedding Model Isolation and Rebuild Strategy (Superseded / Resolved by enabling standard Vector DBs)
