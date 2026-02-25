@echo off
setlocal
chcp 65001 > nul

echo =========================================
echo LogicHive Deployment Launcher
echo =========================================
echo [1] Deploy Edge to GitHub (Release EXE)
echo [0] Exit
echo =========================================

set /p target="Select deployment option (0-1): "

if "%target%"=="1" (
    echo.
    echo Starting Edge Deployment...
    uv run python dev_tools\cd_github.py
) else if "%target%"=="0" (
    echo Exiting...
) else (
    echo Invalid option selected.
)

pause
