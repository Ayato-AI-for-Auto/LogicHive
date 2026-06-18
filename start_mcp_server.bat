@echo off
echo ==========================================
echo LogicHive: MCPサーバー起動
echo ==========================================

:: 仮想環境の確認
if not exist .venv (
    echo [!] 仮想環境が見つかりません。先に dev_setup.bat を実行してください。
    pause
    exit /b 1
)

:: PYTHONPATHの設定（ソースディレクトリを認識させるため）
set PYTHONPATH=src

:: MCPサーバーの起動
uv run python src/mcp_server.py
pause
