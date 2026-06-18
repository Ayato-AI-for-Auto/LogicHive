@echo off
echo ==========================================
echo LogicHive: 設定ツール (Settings UI)
echo ==========================================

:: 仮想環境の確認
if not exist .venv (
    echo [!] 仮想環境が見つかりません。先に dev_setup.bat を実行してください。
    pause
    exit /b 1
)

:: 設定UIの起動
uv run python src/settings_ui.py
pause
