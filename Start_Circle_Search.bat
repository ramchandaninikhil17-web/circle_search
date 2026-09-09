@echo off
cd /d "%~dp0"
set "ARGS=%*"
if "%ARGS%"=="" set "ARGS=--tray"

if exist "%~dp0dist\CircleSearch.exe" (
    start "" "%~dp0dist\CircleSearch.exe" %ARGS%
    exit /b 0
)

for %%V in (Python314 Python313 Python312 Python311 Python310) do (
    if exist "%LOCALAPPDATA%\Programs\Python\%%V\pythonw.exe" (
        start "" "%LOCALAPPDATA%\Programs\Python\%%V\pythonw.exe" main.py %ARGS%
        exit /b 0
    )
)
start "" pythonw main.py %ARGS%
