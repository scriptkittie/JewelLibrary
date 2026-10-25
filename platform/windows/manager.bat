@echo off
setlocal EnableExtensions
set "SDJ_INSTALL=%LOCALAPPDATA%\SteamDeckJewels"

:menu
cls
echo ========================================
echo       SteamDeck Jewels Setup Manager
echo ========================================
echo.
echo Install location: %SDJ_INSTALL%
echo.
echo   1. Install / Update from this download
echo   2. Update from GitHub (latest release)
echo   3. Update from a ZIP
echo   4. Repair installation
echo   5. Check installation
echo   6. Launch SteamDeck Jewels
echo   7. Open SDJ folder
echo   8. Exit
echo.
set "SDJ_CHOICE="
set /p "SDJ_CHOICE=Choose an option [1-8]: "

if "%SDJ_CHOICE%"=="1" (
    call "%~dp0setup.bat" update
    pause
    goto :menu
)
if "%SDJ_CHOICE%"=="2" goto :github
if "%SDJ_CHOICE%"=="3" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0update-from-zip.ps1" -InstallDir "%SDJ_INSTALL%"
    pause
    goto :menu
)
if "%SDJ_CHOICE%"=="4" (
    call "%~dp0setup.bat" repair
    pause
    goto :menu
)
if "%SDJ_CHOICE%"=="5" goto :check
if "%SDJ_CHOICE%"=="6" (
    if exist "%SDJ_INSTALL%\platform\windows\run.bat" start "" "%SDJ_INSTALL%\platform\windows\run.bat"
    if not exist "%SDJ_INSTALL%\platform\windows\run.bat" echo SteamDeck Jewels is not installed yet.
    goto :menu
)
if "%SDJ_CHOICE%"=="7" goto :open
if "%SDJ_CHOICE%"=="8" exit /b 0
echo Invalid choice.
pause
goto :menu

:github
rem The update replaces this menu's own file, so it runs in its own window and this menu closes.
set "SDJ_PY=%SDJ_INSTALL%\.venv\Scripts\python.exe"
if not exist "%SDJ_PY%" set "SDJ_PY=py"
start "SteamDeck Jewels Update" "%SDJ_PY%" "%~dp0..\..\tools\update_from_github.py" --install "%SDJ_INSTALL%" --pause
exit /b 0

:check
echo.
if exist "%SDJ_INSTALL%\src\steamdeck_jewels\app.py" (
    echo [OK] Application source
) else (
    echo [MISSING] Application source
)
if exist "%SDJ_INSTALL%\data\games.json" (echo [OK] Game database) else (echo [INFO] Game database is created the first time you open SteamDeck Jewels)
if exist "%SDJ_INSTALL%\assets\covers" (echo [OK] Cover library) else (echo [MISSING] Cover library)
if exist "%SDJ_INSTALL%\.venv\Scripts\python.exe" (echo [OK] Python environment) else (echo [MISSING] Python environment)
if exist "%USERPROFILE%\Desktop\SteamDeck Jewels.lnk" (echo [OK] Desktop shortcut) else (echo [CHECK] Desktop shortcut not found at the standard path)
echo.
pause
goto :menu

:open
if not exist "%SDJ_INSTALL%" (
    echo SteamDeck Jewels is not installed yet.
    pause
    goto :menu
)
start "" explorer.exe "%SDJ_INSTALL%"
goto :menu
