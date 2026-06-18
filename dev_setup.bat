@echo off
setlocal
echo ==========================================
echo LogicHive: 開発用仮想環境構築 (uv)
echo ==========================================

:: uvの確認
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] 'uv' がインストールされていません。
    echo https://github.com/astral-sh/uv からインストールしてください。
    pause
    exit /b 1
)

:: 仮想環境の作成
echo [1/2] 仮想環境 (.venv) を作成中...
if not exist .venv (
    uv venv .venv
) else (
    echo [i] .venv は既に存在します。
)

:: 依存関係のインストール
echo [2/2] 依存関係を編集可能モード (-e .) でインストール中...
uv pip install -e .

echo.
echo ✅ 構築が完了しました！
pause
