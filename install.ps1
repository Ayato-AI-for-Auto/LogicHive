# LogicHive: Professional One-Click Installer for Windows
# Usage: powershell -ExecutionPolicy Bypass -File install.ps1

$projectName = "LogicHive"
$installRoot = "$env:LOCALAPPDATA\$projectName"

Write-Host "--- $projectName: Professional Setup ---" -ForegroundColor Cyan

# 1. Ensure Directory
if (!(Test-Path $installRoot)) {
    New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
}

# 2. Check if we are in the repository or running standalone
$currentDir = Get-Location
if (Test-Path "$currentDir\LogicHive.exe") {
    Write-Host "[INFO] Local executable found. Installing to $installRoot..."
    Copy-Item "LogicHive.exe" "$installRoot\" -Force
    $exePath = "$installRoot\LogicHive.exe"
}
elseif (Test-Path "$currentDir\backend\edge\mcp_server.py") {
    Write-Host "[INFO] Running from source environment."
    if (!(Get-Command "uv" -ErrorAction SilentlyContinue)) {
        Write-Error "Python manager 'uv' not found. Please install it first or use the standalone EXE."
        exit 1
    }
    uv run logic-hive-setup
    Write-Host "[SUCCESS] LogicHive (Source) configured." -ForegroundColor Green
    exit 0
}
else {
    Write-Host "[INFO] Standalone installation mode."
    # Future: Download from GitHub Releases
    # Invoke-WebRequest -Uri "https://github.com/Ayato-AI-for-Auto/LogicHive/releases/latest/download/LogicHive-Windows.zip" -OutFile "$installRoot\release.zip"
    # Expand-Archive "$installRoot\release.zip" -DestinationPath $installRoot -Force
    Write-Error "Please run this script from the LogicHive folder or a release ZIP."
    exit 1
}

# 3. Generate Config using the EXE
Write-Host "[INFO] Generating MCP Configuration..."
& $exePath --generate-mcp-config

Write-Host "`n[SUCCESS] $projectName has been installed and configured!" -ForegroundColor Green
Write-Host "You can now add 'mcp_config_logic_hive.json' to your Cursor / Gemini Desktop settings."
