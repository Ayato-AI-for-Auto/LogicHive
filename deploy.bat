@echo off
setlocal
chcp 65001 > nul

echo =========================================
echo LogicHive Unified CD Launcher
echo =========================================
echo [1] Deploy Edge to GitHub (cd_github.py)
echo [2] Deploy Hub to GCP (deploy.py)
echo [3] Deploy Both
echo [0] Exit
echo =========================================

set /p target="Select deployment option (0-3): "

if "%target%"=="1" (
    echo.
    echo Starting Edge Deployment...
    uv run python dev_tools\cd_github.py
) else if "%target%"=="2" (
    echo.
    echo Starting GCP Hub Deployment...
    uv run python dev_tools\deploy.py
) else if "%target%"=="3" (
    echo.
    echo Starting Edge Deployment...
    uv run python dev_tools\cd_github.py
    echo.
    echo Starting GCP Hub Deployment...
    uv run python dev_tools\deploy.py
) else if "%target%"=="0" (
    echo Exiting...
) else (
    echo Invalid option selected.
)

pause
