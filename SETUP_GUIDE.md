# Function Store MCP セットアップガイド

このMCPサーバーは、AIエージェントが過去に書いたPython関数を記憶（保存）し、検索・再利用するための究極のツールです。
TypeScriptによるプロキシを介しているため、`npx` コマンドだけで簡単に導入できます。

## 1. 前提条件
- **Node.js**: `v18` 以上
- **uv**: Python環境管理ツール。未インストールの場合は [こちら](https://github.com/astral-sh/uv) からインストールしてください。

## 2. エディタへの登録方法

### Cursor の場合
1. Cursorの設定（Settings）を開きます。
2. `General` > `MCP` セクションを探します。
3. `+ Add New MCP Server` をクリックします。
4. 以下の情報を入力して保存します：
   - **Name**: `FunctionStore`
   - **Type**: `command`
   - **Command**: `npx -y @ayato-ai/function-store-mcp@latest`

### Claude Desktop の場合
1. `config.json`（通常は `%APPDATA%/Claude/claude_desktop_config.json`）を開きます。
2. `mcpServers` セクションに以下を追加します：

```json
{
  "mcpServers": {
    "function-store": {
      "command": "npx",
      "args": ["-y", "@ayato-ai/function-store-mcp@latest"]
    }
  }
}
```

## 3. 使い方
登録が完了したら、AIエージェントにこう話しかけてみてください：
- 「この関数を FunctionStore に保存して」
- 「JSONパース用のロジックを FunctionStore から探して」
- 「アーカイブした関数をリストアップして」

バックグラウンドでPythonサーバーが自動起動し、ベクトル検索や依存関係の解決が実行されます。
