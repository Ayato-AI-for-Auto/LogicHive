# ADR-0015: Lightweight Ephemeral Environments & GC

- **Date**: 2026-06-03
- **Status**: Accepted
- **Deciders**: ayato-labs (via Agent)

## Context
LogicHive の機能検証において、Pythonコードの安全な実行のために `EphemeralPythonExecutor` を使用しています。しかし、毎回の検証ごとに隔離された仮想環境（`venv`）をフルスクラッチで作成し、そこに PyTorch などの巨大なライブラリをコピー（またはダウンロード）していました。
さらに、実行完了後にこれらの環境を破棄するメカニズム（ガベージコレクション）が欠如していたため、`storage/data/pools/` 配下に12万ファイル、4.4GBを超える残骸が蓄積し（ストレージリーク）、後続の監査ツールやシステムパフォーマンスに致命的な遅延をもたらしていました。

## Decision
1. **Lightweight Environment (環境の軽量化)**:
   仮想環境作成時に `python -m venv --system-site-packages` をデフォルトで使用します。これにより、ホスト環境（またはベースの venv）にインストール済みの巨大なライブラリ（PyTorch, NumPyなど）をシンボリックリンク的に参照するようになり、環境作成時のディスクI/Oと容量消費を極限まで削減します。
2. **Strict Garbage Collection (厳格なクリーンアップ)**:
   `EphemeralPythonExecutor` の実行ライフサイクルにおいて、`try...finally` ブロックを強制し、プロセスの成功・失敗（タイムアウトや構文エラー含む）に関わらず、最後に関数 `self._cleanup()` を呼び出して環境ディレクトリを物理削除（`shutil.rmtree`）する責任を持たせます。

## Consequences
### Positive
- **劇的な高速化**: 環境構築にかかる時間が数秒から数十ミリ秒に短縮されます。
- **ストレージ容量の節約**: 何十回テストを実行してもディスク容量が増加しなくなります。
- **システムの安定性**: 監査ツールが自動生成物の海で溺れることがなくなり、高速に動作するようになります。

### Negative / Risks
- **環境汚染の微小なリスク**: `--system-site-packages` を使用するため、実行されたコードがサイトパッケージの深い部分を操作しようとした場合、稀にホスト環境に影響を与えるリスクがあります。しかし、ローカルファーストな個人のロジックVaultという性質上、悪意のあるサードパーティコードを直接実行するケースは少なく、このトレードオフは許容可能です。

## References
- Issue: Storage Leak in Verification Pools
- ADR-0014: standardized-hybrid-configuration-strategy
