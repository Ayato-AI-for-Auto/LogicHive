@echo off
setlocal
pushd "%~dp0"

echo ==========================================
echo LogicHive: Settings Configuration
echo ==========================================
echo.

:: Check for .venv
if not exist .venv goto no_venv

:: Set PYTHONPATH to support both root and src-based imports
set PYTHONPATH=.;src

:: Run settings UI
uv run python src/settings_ui.py
if %errorlevel% neq 0 goto err_run

goto end

:no_venv
echo [ERROR] Virtual environment (.venv) not found.
echo Please run setup.bat first to initialize the environment.
pause
exit /b 1

:err_run
echo.
echo [ERROR] Settings UI exited with error code %errorlevel%.
pause
exit /b 1

:end
popd
pause
