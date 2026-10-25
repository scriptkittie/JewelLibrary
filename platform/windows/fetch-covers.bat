@echo off
setlocal
for %%I in ("%~dp0..\..") do set "SDJ_ROOT=%%~fI"
if not exist "%SDJ_ROOT%\.venv\Scripts\python.exe" (
    echo The Python environment is missing. Run setup-windows.bat or run-windows.bat first.
    pause
    exit /b 1
)
"%SDJ_ROOT%\.venv\Scripts\python.exe" "%SDJ_ROOT%\tools\covers\fetch_covers.py"
pause
