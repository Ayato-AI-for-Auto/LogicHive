@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo 🚀 LogicHive: Launch System
echo ==========================================

:: 1. Check for environment
if not exist .venv (
    echo [!] .venv not found. Please run setup.bat first.
    pause
    exit /b 1
)

:: 2. Load .env variables (Simple parser for Windows batch)
if exist .env (
    for /f "usebackq tokens=1* delims==" %%i in (".env") do (
        set "%%i=%%j"
    )
)

:: 3. Launch Server
echo [i] Starting LogicHive MCP Server...
echo.

:: We use 'uv run' to ensure the .venv is active and dependencies are correct
uv run python src/mcp_server.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Server stopped with error code %errorlevel%.
    pause
)
