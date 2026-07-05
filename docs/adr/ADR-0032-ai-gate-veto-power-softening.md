# ADR-0032: AI Gate Veto Power Softening and Weight Tuning

- **Date**: 2026-07-05
- **Status**: Accepted
- **Deciders**: ayato-labs (User), opencode/mimo-v2.5-free (Agent)

## Context

LogicHive の品質ゲート（Quality Gate）は、保存されたナレッジの品質を保証するために複数の評価プラグインを組み合わせて `reliability_score` を算出する。
現在の重み付けは：

| プラグイン | 重み | 役割 |
|-----------|------|------|
| Deterministic (AST) | 30% | アサーション、ホロ判定 |
| Runtime | 30% | テスト実行 |
| Static Analysis | 20% | 構造解析、Ruff、セキュリティ |
| AI Gate | 15% | LLM品質評価 |
| Metrics Gate | 5% | 循環複雑度 |

### 課題 1: AI Gate の Veto 権限が過剰
現在の `manager.py:337-349` のロジック：

```python
if ai_res.score < 30:
    final_score = 0.0  # ハードリジェクト（Veto）
elif ai_res.score < 70:
    final_score = min(final_score, ai_res.score)  # ハードキャップ
```

- **問題**: AI Gate のスコアが30未満の場合、他の全評価が100点でも `reliability_score` が 0.0 に強制される。
- **影響**: 確定的な静的解析・ランタイムテストで高得点を取ったコードも、LLM の一時的な判断ミスで拒否される。

### 課題 2: システムエラー時の Veto
- `AIGateEvaluator` は LLM 接続失敗時（API キー無効、ネットワーク障害、レート制限）に `score=0.0, is_system_error=True` を返す。
- 現行ロジックでは `is_system_error` が無視され、`score < 30` で Veto が発動する。
- **結果**: LLM 基盤障害時に、正常なコードが不正に拒否される。

### 課題 3: AI Gate の重みが相対的に大きい
- 重み 15% は他プラグインと比較して大きく、AI Gate のスコアが最終スコアに大きく影響する。
- 特に LLM は非決定的（nondeterministic）であるため、同じコードでも回によって異なるスコアを返す可能性がある。

## Decision

### 1. AI Gate 重みの削減（15% → 10%）
- `core/evaluation/manager.py:306-312` の `mapping` で `ai_gate` の重みを `0.10` に変更。
- `.env` で `AI_GATE_WEIGHT` を設定可能にし、運用者が調整できるようにする。
- 重みの合計が1.0になるよう、他の重みは変更しない（不足分は `total_weight` で正規化）。

### 2. Veto ロジックの軟化
- `score < 30` のハードリジェクト → 50%減衰に変更。
  ```python
  if ai_res.score < 30:
      final_score *= 0.5  # 50%減衰（Veto廃止）
  ```
- `score < 70` のハードキャップ → ソフトキャップに変更。
  ```python
  elif ai_res.score < 70:
      final_score = min(final_score, ai_res.score * 1.2)  # 20%緩和
  ```

### 3. システムエラー時の Veto 回避
- `is_system_error=True` の場合、Veto ロジックを完全にスキップする。
- ログにシステムエラーの詳細を記録し、運用上の可視性を確保する。
- `EvaluationResult.score` を `Optional[float]` に変更し、システムエラー時は `score=None` を返すようにする。
  - `manager.py` 側で `score is None` なら Veto 対象外にする。
  - スコア算出でも `None` は無視され、他の評価のみでスコアが決まる。

## Consequences

### Positive
- **過剰リジェクトの解消**: 確定的評価で高得点を取ったコードが、LLM の主観的評価で不当に拒否されなくなる。
- **インフラ障害への耐性**: LLM 基盤障害時でも、正常なコードは保存可能になる。
- **運用柔軟性**: `.env` で重みを調整できるため、品質基準のカスタマイズが可能。

### Negative / Risks
- **品質低下リスク**: AI Gate の重み削減により、LLM が捕捉できた品質問題が見逃される可能性がある。
  - Mitigation: Deterministic（30%）+ Runtime（30%）で60%を占めるため、主要な品質保証は維持。
- **50%減衰の妥当性**: `score < 30` で半分にするロジックは、暫定的な値。運用で効果を観察し、必要に応じて調整。

## References
- Issue: AI Gate veto power too strong
- ADR-0021: Score-Scaled Multiplicative RAG Prioritization — 重み定義の変更を反映
- `core/evaluation/manager.py:302-349` — 現行スコアリング + Veto ロジック
- `core/evaluation/plugins/ai.py:22-33` — AI Gate evaluator

## Amendment: Deterministic + Runtime 60% の根拠

品質保証の二本柱は **「事実ベースの検証」** である：
- **Deterministic (30%)**: AST 解析によるアサーション、ホロ判定など、コードの構造的事実を検証。LLM に依存しない。
- **Runtime (30%)**: 実際のコード実行によるテスト結果。最も信頼性の高い検証手段。

これら合計60%が LLM に依存しないため、AI Gate の影響力削減でも品質基準は維持される。
AI Gate は「品質の参考情報」として位置づけ、最終判断には確定的評価を優先する。
