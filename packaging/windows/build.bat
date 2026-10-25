@echo off
rem Build the Windows app with PyInstaller, then the installer if Inno Setup 6 is installed.
setlocal
for %%I in ("%~dp0..\..") do set "SDJ_ROOT=%%~fI"
cd /d "%SDJ_ROOT%"
if not exist ".build-venv\Scripts\python.exe" py -3 -m venv .build-venv || goto :error
".build-venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller || goto :error
".build-venv\Scripts\pyinstaller.exe" --noconfirm --clean SteamDeckJewels.spec || goto :error
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
for /f "delims=" %%V in ('.build-venv\Scripts\python.exe -c "import sys;sys.path.insert(0,'src');import steamdeck_jewels;print(steamdeck_jewels.__version__)"') do set "SDJ_VERSION=%%V"
if exist "%ISCC%" (
    "%ISCC%" /DAppVersion=%SDJ_VERSION% packaging\windows\installer.iss || goto :error
    echo Built release\SteamDeckJewels-Setup.exe
) else (
    echo Built dist\SteamDeckJewels\SteamDeckJewels.exe. Install Inno Setup 6 to also build the installer.
)
exit /b 0
:error
echo Build failed.
exit /b 1
