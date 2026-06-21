@echo off
setlocal
pushd "%~dp0"

echo ==========================================
echo LogicHive: MCPサーバー起動 (Streamable HTTP)
echo ==========================================
echo.

:: 仮想環境の確認
if not exist .venv (
    echo [!] 仮想環境が見つかりません。先に setup.bat を実行してください。
    pause
    exit /b 1
)

:: PYTHONPATHの設定（ソースディレクトリを認識させるため）
set PYTHONPATH=src

:: MCPサーバーの起動
uv run python src/mcp_server.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] サーバーがエラーコード %errorlevel% で終了しました。
    pause
    exit /b 1
)

popd
pause
