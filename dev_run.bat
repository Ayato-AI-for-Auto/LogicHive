@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo 🚀 LogicHive Hub: Development Launcher
echo ==========================================

:: 1. Ensure environment is ready
echo [1/2] Checking environment...
if not exist .venv (
    echo [!] .venv not found. Please run 'uv sync' first.
    exit /b 1
)

:: 2. Launch Server
:: The application itself handles port conflicts interactively via core.network.recovery.
:: We simply launch the server using uv.
echo [2/2] Launching LogicHive Hub...
echo.

uv run src/mcp_server.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Server exited with error code %errorlevel%.
    pause
)
