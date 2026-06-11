@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo 🚀 LogicHive Hub: MCP Server Launcher
echo ==========================================

:: 1. Setup Environment
echo [1/2] Setting up environment...
set PYTHONPATH=src
if not exist .venv (
    echo [!] .venv not found. Please run 'uv sync' first.
    exit /b 1
)

:: 2. Launch Server
echo [2/2] Launching LogicHive Hub MCP Server...
echo [i] Running: uv run python src/mcp_server.py
echo.
uv run python src/mcp_server.py

echo.
echo ==========================================
echo Server stopped.
echo ==========================================
pause
