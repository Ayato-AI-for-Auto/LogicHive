@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo 🚀 LogicHive Hub: Development Launcher
echo ==========================================

:: 1. Cleanup existing processes (Port 10880)
echo [1/3] Checking for conflicting processes on port 10880...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :10880 ^| findstr LISTENING') do (
    echo [!] Found process with PID %%a. Terminating...
    taskkill /F /PID %%a >nul 2>&1
)

:: 2. Setup Environment
echo [2/3] Setting up environment...
set PYTHONPATH=src
if not exist .venv (
    echo [!] .venv not found. Please run 'uv sync' first.
    exit /b 1
)

:: 3. Launch Server
echo [3/3] Launching LogicHive Hub...
echo Model: %GEMINI_MODEL% (from .env)
echo.
uv run src/mcp_server.py

pause
