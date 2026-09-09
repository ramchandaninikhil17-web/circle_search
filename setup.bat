@echo off
setlocal enabledelayedexpansion
title Circle to Search - 1-Click Setup
cd /d "%~dp0"

echo ===================================================
echo     Circle to Search for Windows - Quick Setup
echo ===================================================
echo.

REM 1. Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [!] Python was not found on your system.
        echo.
        echo Please install Python 3.10 or higher from:
        echo   https://www.python.org/downloads/
        echo Make sure to check "Add python.exe to PATH" during install!
        echo.
        pause
        exit /b 1
    )
    set "PY_CMD=py"
) else (
    set "PY_CMD=python"
)

echo [*] Python found! Installing required libraries...
%PY_CMD% -m pip install --upgrade pip >nul 2>nul
%PY_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] Failed to install dependencies. Please check your internet connection.
    pause
    exit /b 1
)
echo [OK] Dependencies installed successfully.
echo.

REM 2. Create Desktop and Start Menu Shortcuts
echo [*] Creating Desktop and Start Menu shortcuts...
%PY_CMD% create_shortcut.py
echo.

REM 3. Launch App
echo [*] Starting Circle to Search in system tray...
start "" Start_Circle_Search.bat
echo.
echo ===================================================
echo   Setup Complete!
echo   Press [Ctrl + Shift + S] anytime to search!
echo ===================================================
echo.
timeout /t 5 >nul
exit /b 0
