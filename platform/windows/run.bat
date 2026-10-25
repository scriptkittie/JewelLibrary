@echo off
setlocal
for %%I in ("%~dp0..\..") do set "SDJ_ROOT=%%~fI"
if not exist "%SDJ_ROOT%\.venv\Scripts\pythonw.exe" (
    echo First run: creating a private Python environment in %SDJ_ROOT%\.venv ...
    py -3 -m venv "%SDJ_ROOT%\.venv" || goto :python_error
    "%SDJ_ROOT%\.venv\Scripts\python.exe" -m pip install --upgrade pip || goto :error
    "%SDJ_ROOT%\.venv\Scripts\python.exe" -m pip install -r "%SDJ_ROOT%\requirements.txt" || goto :error
)
set "PYTHONPATH=%SDJ_ROOT%\src"
start "SteamDeck Jewels" /D "%SDJ_ROOT%" "%SDJ_ROOT%\.venv\Scripts\pythonw.exe" -m steamdeck_jewels --windowed
exit /b 0
:python_error
echo Python 3 was not found. Install Python from python.org and include the Python Launcher.
:error
echo Could not prepare the Python environment.
pause
exit /b 1
