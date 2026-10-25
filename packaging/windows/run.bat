@echo off
rem Run SteamDeck Jewels from the source code (for development). Uses the repository's data\ folder.
setlocal
for %%I in ("%~dp0..\..") do set "SDJ_ROOT=%%~fI"
if not exist "%SDJ_ROOT%\.venv\Scripts\pythonw.exe" (
    echo Creating a Python environment in %SDJ_ROOT%\.venv ...
    py -3 -m venv "%SDJ_ROOT%\.venv" || goto :error
    "%SDJ_ROOT%\.venv\Scripts\python.exe" -m pip install -r "%SDJ_ROOT%\requirements.txt" || goto :error
)
set "PYTHONPATH=%SDJ_ROOT%\src"
start "SteamDeck Jewels" /D "%SDJ_ROOT%" "%SDJ_ROOT%\.venv\Scripts\pythonw.exe" -m steamdeck_jewels --windowed
exit /b 0
:error
echo Could not prepare the Python environment. Install Python 3 from python.org with the py launcher.
pause
exit /b 1
