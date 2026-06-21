@echo off
setlocal
pushd "%~dp0"

echo ==========================================
echo LogicHive: 設定ツール (Settings UI)
echo ==========================================
echo.

:: 仮想環境の確認
if not exist .venv (
    echo [!] 仮想環境が見つかりません。先に setup.bat を実行してください。
    pause
    exit /b 1
)

:: 設定UIの起動
uv run python src/settings_ui.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 設定ツールがエラーコード %errorlevel% で終了しました。
    pause
    exit /b 1
)

popd
pause
