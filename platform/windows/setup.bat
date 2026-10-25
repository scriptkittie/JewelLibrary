@echo off
setlocal EnableExtensions
for %%I in ("%~dp0..\..") do set "SDJ_SOURCE=%%~fI"
if not defined SDJ_INSTALL set "SDJ_INSTALL=%LOCALAPPDATA%\SteamDeckJewels"
set "SDJ_MODE=%~1"
if not defined SDJ_MODE set "SDJ_MODE=update"
echo %SDJ_MODE% SteamDeck Jewels at %SDJ_INSTALL%
for %%I in ("%SDJ_INSTALL%") do set "SDJ_INSTALL_FULL=%%~fI"
if /I "%SDJ_SOURCE%"=="%SDJ_INSTALL_FULL%" (
    echo Running from the installed copy, so there are no new files to copy.
    echo To update the app itself, run setup-windows.bat from the downloaded or GitHub folder.
    echo Refreshing the Python environment and shortcuts instead...
    goto :environment
)
if not exist "%SDJ_INSTALL%\src" mkdir "%SDJ_INSTALL%\src" || goto :error
if not exist "%SDJ_INSTALL%\platform\windows" mkdir "%SDJ_INSTALL%\platform\windows" || goto :error
xcopy "%SDJ_SOURCE%\src\*" "%SDJ_INSTALL%\src\" /E /I /Y /Q >nul || goto :error
xcopy "%SDJ_SOURCE%\tools\*" "%SDJ_INSTALL%\tools\" /E /I /Y /Q >nul || goto :error
xcopy "%SDJ_SOURCE%\docs\*" "%SDJ_INSTALL%\docs\" /E /I /Y /Q >nul || goto :error
xcopy "%SDJ_SOURCE%\platform\windows\*" "%SDJ_INSTALL%\platform\windows\" /E /I /Y /Q >nul || goto :error
copy /Y "%SDJ_SOURCE%\requirements.txt" "%SDJ_INSTALL%\requirements.txt" >nul || goto :error
rem The library files in data\ are created by the app on first launch and never overwritten here.
if not exist "%SDJ_INSTALL%\data" mkdir "%SDJ_INSTALL%\data" || goto :error
if not exist "%SDJ_INSTALL%\assets" (
    xcopy "%SDJ_SOURCE%\assets\*" "%SDJ_INSTALL%\assets\" /E /I /Y /Q >nul || goto :error
) else (
    xcopy "%SDJ_SOURCE%\assets\*" "%SDJ_INSTALL%\assets\" /E /I /D /Y /Q >nul
)
if not exist "%SDJ_INSTALL%\reports" xcopy "%SDJ_SOURCE%\reports\*" "%SDJ_INSTALL%\reports\" /E /I /Y /Q >nul
:environment
if not exist "%SDJ_INSTALL%\.venv\Scripts\python.exe" py -3 -m venv "%SDJ_INSTALL%\.venv" || goto :python_error
"%SDJ_INSTALL%\.venv\Scripts\python.exe" -m pip install --upgrade pip || goto :error
if /I "%SDJ_MODE%"=="repair" (
    "%SDJ_INSTALL%\.venv\Scripts\python.exe" -m pip install --force-reinstall -r "%SDJ_INSTALL%\requirements.txt" || goto :error
) else (
    "%SDJ_INSTALL%\.venv\Scripts\python.exe" -m pip install -r "%SDJ_INSTALL%\requirements.txt" || goto :error
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SDJ_SOURCE%\platform\windows\create-shortcut.ps1" -InstallDir "%SDJ_INSTALL%" || goto :error
echo Setup complete. Use the SteamDeck Jewels shortcut on your Desktop.
exit /b 0
:python_error
echo Python 3 was not found. Install Python from python.org and include the Python Launcher.
:error
echo SteamDeck Jewels setup failed.
rem The in-app updater runs setup hidden and reads its log, so it must not wait for a key.
if not defined SDJ_NONINTERACTIVE pause
exit /b 1
