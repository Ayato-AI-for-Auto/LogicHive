# ADR-0013: 手動タスクスケジューラー設定の採用

- **Date**: 2026-05-31
- **Status**: Superseded by [ADR-0016](./ADR-0016-os-integration-and-clean-uninstall-strategy.md)
- **Deciders**: ユーザー, Gemini CLI

## Context
LogicHiveの常駐機能（自動起動）を実現するために、アプリケーション内にタスクスケジューラーへの登録・削除機能を実装する案が浮上した。
しかし、これは以下の懸念がある：
1. 管理者権限（UAC昇格）のUI実装によるコードの複雑化と攻撃表面の拡大。
2. OS依存のスケジューラー操作による将来的な保守コストの増大。
3. 開発リソースを本来の機能強化に割くべきという優先順位の判断。

## Decision
アプリケーション内に自動登録・削除機能を実装することはせず、ユーザー自身がWindows標準ツールまたはPowerShellを用いて設定を行う方針を採用する。
設定手順は README.md に明記し、ユーザーの利便性を確保する。

## Consequences
### Positive
- アプリケーションコードの複雑度を低減。
- セキュリティリスク（特権昇格）を排除。
- 開発リソースを最優先事項へ集中。
### Negative / Risks
- 初心者ユーザーにとっての導入障壁がわずかに高まる。

## References
- Issue: N/A
- PR: N/A
