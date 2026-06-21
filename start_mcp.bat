@echo off
setlocal
pushd "%~dp0"

echo ==========================================
echo LogicHive: Starting MCP Server (Streamable HTTP)
echo ==========================================
echo.

:: Check for .venv
if not exist .venv goto no_venv

:: Set PYTHONPATH to support both root and src-based imports
set PYTHONPATH=.;src

:: Start the MCP server
uv run python src/mcp_server.py
if %errorlevel% neq 0 goto err_run

goto end

:no_venv
echo [ERROR] Virtual environment (.venv) not found.
echo Please run setup.bat first to initialize the environment.
pause
exit /b 1

:err_run
echo.
echo [ERROR] Server exited with error code %errorlevel%.
pause
exit /b 1

:end
popd
pause
