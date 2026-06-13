# ADR-0028: バイナリ配布環境における動的リソースのパス解決戦略

- **Date**: 2026-06-13
- **Status**: Accepted
- **Deciders**: Gemini CLI (Auto-Edit Mode)

## Context
LogicHiveは、評価プラグイン（Evaluators）を `plugins` ディレクトリから動的にロードする仕組みを採用している。
しかし、PyInstallerを用いてアプリケーションを単一のバイナリ（exe）にパッケージ化した場合、実行時にリソースが一時ディレクトリ（`sys._MEIPASS`）に展開される。

従来の相対パス解決ロジック（`os.path.dirname(__file__)` 依存）では、バイナリ実行時にこの一時展開先を正しく参照できず、プラグインのロードに失敗し、システムの核心である「品質ゲート」が機能しなくなるという問題が発生した。

## Decision
バイナリ実行環境（Frozen環境）と開発環境の両方で、確実に動的リソースを検出できるよう、以下のパス解決戦略を導入する。

1.  **実行環境の判定**: `sys.frozen` 属性の有無を確認し、パッケージ化されたバイナリとしての実行かどうかを判別する。
2.  **一時展開先の優先参照**: バイナリ実行時は、PyInstallerが提供する一時ディレクトリ `sys._MEIPASS` を基点としてリソースを探す。
3.  **多層構造への対応**: ビルド設定（.spec）によるディレクトリ構造の変化に耐えられるよう、複数の想定パス（`core/evaluation/plugins` および `src/core/evaluation/plugins`）を順次確認する。
4.  **開発環境へのフォールバック**: 非バイナリ実行時は、従来通りソースファイルからの相対パスを使用する。

## Consequences
### Positive
- バイナリ配布版においても、品質ゲート（セキュリティスキャン、実行検証等）が完全に動作するようになる。
- リソース位置の誤認による実行時エラー（FileNotFoundError）を排除できる。
- 今後、他の動的リソース（設定テンプレート等）を追加する際の標準的な実装パターンが確立された。

### Negative / Risks
- `sys._MEIPASS` などの特定のパッケージングツールに依存したコードが含まれる（ただし、条件分岐により非バイナリ環境への影響はゼロである）。

## References
- Issue: EvaluationManager: Plugins directory not found
- File: `src/core/evaluation/manager.py`
- Related ADR: ADR-0011 (Dual Binary Separation)
