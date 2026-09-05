@echo off
cd /d "%~dp0"
set "ARGS=%*"
if "%ARGS%"=="" set "ARGS=--tray"

set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
if exist "%PY_EXE%" (
    start "" "%PY_EXE%" main.py %ARGS%
    exit
)
start "" pythonw main.py %ARGS%
