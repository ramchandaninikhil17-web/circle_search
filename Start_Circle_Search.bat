@echo off
cd /d "%~dp0"
set "ARGS=%*"
if "%ARGS%"=="" set "ARGS=--tray"

for %%V in (Python314 Python313 Python312 Python311 Python310) do (
    if exist "%LOCALAPPDATA%\Programs\Python\%%V\pythonw.exe" (
        start "" "%LOCALAPPDATA%\Programs\Python\%%V\pythonw.exe" main.py %ARGS%
        exit /b 0
    )
)
start "" pythonw main.py %ARGS%
