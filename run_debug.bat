@echo off
cd /d "%~dp0"
echo Starting Circle to Search in debug/console mode...
echo Press Ctrl+Shift+S to trigger Circle to Search.
echo Look for the icon in your Windows System Tray (near the clock).
echo.

set "FOUND_PY="
for %%V in (Python314 Python313 Python312 Python311 Python310) do (
    if not defined FOUND_PY (
        if exist "%LOCALAPPDATA%\Programs\Python\%%V\python.exe" (
            set "FOUND_PY=%LOCALAPPDATA%\Programs\Python\%%V\python.exe"
        )
    )
)

if defined FOUND_PY (
    "%FOUND_PY%" main.py %*
) else (
    python main.py %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Circle to Search stopped with an error code: %ERRORLEVEL%
)
pause
