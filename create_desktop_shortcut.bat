@echo off
title Create Circle to Search Shortcuts
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% equ 0 (
    python create_shortcut.py
    pause
    exit /b 0
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py create_shortcut.py
    pause
    exit /b 0
)

for %%V in (Python314 Python313 Python312 Python311 Python310) do (
    if exist "%LOCALAPPDATA%\Programs\Python\%%V\python.exe" (
        "%LOCALAPPDATA%\Programs\Python\%%V\python.exe" create_shortcut.py
        pause
        exit /b 0
    )
)

echo [!] Could not locate Python to run create_shortcut.py.
echo Creating shortcut using PowerShell...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $d = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut((Join-Path $d 'Circle to Search.lnk')); $s.TargetPath = (Resolve-Path 'dist\CircleSearch.exe').Path; $s.WorkingDirectory = (Get-Location).Path; $s.IconLocation = (Resolve-Path 'app_icon.ico').Path + ',0'; $s.Description = 'Circle to Search - Google Lens for Windows (Ctrl+Shift+S)'; $s.Save(); Write-Host '[OK] Shortcut created on Desktop!'"
pause
