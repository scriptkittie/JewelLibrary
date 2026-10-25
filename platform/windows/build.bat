@echo off
setlocal
for %%I in ("%~dp0..\..") do set "SDJ_ROOT=%%~fI"
cd /d "%SDJ_ROOT%"
if not exist ".build-venv\Scripts\python.exe" py -3 -m venv .build-venv || goto :error
".build-venv\Scripts\python.exe" -m pip install --upgrade pip || goto :error
".build-venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller || goto :error
".build-venv\Scripts\pyinstaller.exe" --noconfirm --clean SteamDeckJewels.spec || goto :error
echo Built Windows preview at dist\SteamDeckJewels\SteamDeckJewels.exe
exit /b 0
:error
echo Windows build failed.
exit /b 1
