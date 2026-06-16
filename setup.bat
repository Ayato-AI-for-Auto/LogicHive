@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo 🛠️  LogicHive: Setup Environment
echo ==========================================

:: 1. Check for uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] 'uv' is not installed or not in PATH.
    echo Please install uv first: https://github.com/astral-sh/uv
    echo.
    echo Or you can install it via PowerShell:
    echo powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b 1
)

:: 2. Create Virtual Environment
echo [1/4] Creating virtual environment...
if not exist .venv (
    uv venv .venv
) else (
    echo [i] .venv already exists, skipping creation.
)

:: 3. Install Dependencies
echo [2/4] Installing dependencies in editable mode...
uv pip install -e .

:: 4. Setup Environment Variables
echo [3/4] Checking .env file...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo [i] Created .env from .env.example. Please check it.
    ) else (
        echo [!] .env.example not found. Please create .env manually.
    )
) else (
    echo [i] .env already exists.
)

:: 5. Initialize Database (Optional but helpful)
echo [4/4] Verifying project structure...
if not exist storage (
    mkdir storage
)

echo.
echo ==========================================
echo ✅ Setup Complete!
echo You can now start the server using launch.bat
echo ==========================================
pause
