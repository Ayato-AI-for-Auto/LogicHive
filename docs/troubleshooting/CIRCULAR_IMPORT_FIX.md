# 循環インポートによる起動エラー (2026-06-13)

## 問題
PyInstallerでバイナリ（exe）化したLogicHiveを起動する際、以下のエラーが発生してクラッシュした。
`ImportError: cannot import name 'handle_port_conflict' from partially initialized module 'core.network' (most likely due to a circular import)`

## 原因
`mcp_server.py` がネットワークユーティリティを利用するために `core.network` をインポートし、一方で `core.network.recovery.py` がポート競合の解決処理のために `mcp_server.py` をインポートするという、双方向の依存関係（循環インポート）が存在していた。

Pythonのモジュール初期化フェーズにおいて、互いが互いの完了を待つ状態となり、正常なインポートが阻害された。

## 解決策
`src/core/network/recovery.py` において、トップレベルでの `import mcp_server` を削除し、`handle_port_conflict` 関数内で必要な時にだけインポートを行う「ローカルインポート（遅延インポート）」手法を採用した。

```python
def handle_port_conflict(current_port: int, host_val: str) -> int:
    import mcp_server  # ここでインポート
    # ... 処理 ...
```

## 今後の予防
- モジュール間の依存関係をグラフ化して監視する。
- 循環インポートの可能性がある設計（互いにUtilityを呼び合う関係）を避け、共通のUtilityは `core.common` や `core.utils` のような依存先の低いモジュールに分離する。
