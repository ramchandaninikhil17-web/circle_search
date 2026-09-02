@echo off
cd /d "%~dp0"
echo Starting Circle to Search in debug/console mode...
echo Press Ctrl+Alt+C to trigger Circle to Search.
echo Look for the icon in your Windows System Tray (near the clock).
echo.
set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if exist "%PY_EXE%" (
    "%PY_EXE%" main.py
) else (
    python main.py
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Circle to Search stopped with an error code: %ERRORLEVEL%
)
pause
