@echo off
REM Builds a single-file, no-console Windows executable.
cd /d "%~dp0"
pip install -r requirements.txt pyinstaller
pyinstaller --noconsole --onefile --icon app_icon.ico --name CircleSearch main.py
echo.
echo Done. Exe is in dist\CircleSearch.exe
echo Add a shortcut to it in shell:startup to run at login (optional).
pause
