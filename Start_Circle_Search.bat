@echo off
cd /d "%~dp0"
set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
if exist "%PY_EXE%" (
    start "" "%PY_EXE%" main.py
    exit
)
start "" pythonw main.py
