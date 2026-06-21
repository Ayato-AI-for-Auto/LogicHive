@echo off
setlocal
pushd "%~dp0"

echo ==========================================
echo LogicHive: 開発用仮想環境構築 (uv)
echo ==========================================
echo.

:: uvの確認
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] 'uv' がインストールされていません。
    echo https://github.com/astral-sh/uv からインストールしてください。
    pause
    exit /b 1
)

:: 仮想環境の作成
echo [1/4] 仮想環境 (.venv) を作成中...
if not exist .venv (
    uv venv .venv
) else (
    echo [i] .venv は既に存在します。
)

:: 依存関係のインストール
echo [2/4] 依存関係を編集可能モード (-e .) でインストール中...
uv pip install -e .

if %errorlevel% neq 0 (
    echo [ERROR] 依存関係のインストールに失敗しました。
    pause
    exit /b 1
)

:: .env ファイルの設定
echo [3/4] .env ファイルを確認中...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [i] .env.example から .env を作成しました。内容を確認してください。
    ) else (
        echo [!] .env.example が見つかりません。手動で .env を作成してください。
    )
) else (
    echo [i] .env は既に存在します。
)

:: ストレージディレクトリの作成
echo [4/4] ディレクトリ構造を確認中...
if not exist storage (
    mkdir storage
)

echo.
echo ✅ 構築が完了しました！
echo configure.bat で設定を行い、start_mcp.bat でサーバーを起動できます。
popd
pause
