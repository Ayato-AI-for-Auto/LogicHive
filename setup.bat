@echo off
setlocal
pushd "%~dp0"

echo ==========================================
echo LogicHive: Developer Setup (uv)
echo ==========================================
echo.

:: Check for uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] 'uv' is not installed or not in PATH.
    echo Please install it from: https://github.com/astral-sh/uv
    pause
    exit /b 1
)

:: Create virtual environment
echo [1/4] Creating virtual environment (.venv)...
if not exist .venv (
    uv venv .venv
) else (
    echo [INFO] .venv already exists.
)

:: Install dependencies
echo [2/4] Installing dependencies in editable mode...
uv pip install -e .

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Configure .env file
echo [3/4] Checking .env configuration...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [INFO] Created .env from .env.example. Please check the values.
    ) else (
        echo [WARNING] .env.example not found. Please create .env manually.
    )
) else (
    echo [INFO] .env already exists.
)

:: Create storage directories
echo [4/4] Verifying directory structure...
if not exist storage (
    mkdir storage
)

echo.
echo Setup completed successfully!
echo Run configure.bat to edit settings, and start_mcp.bat to launch the server.
popd
pause
