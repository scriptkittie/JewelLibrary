; Inno Setup script for the Windows installer (SteamDeckJewels-Setup.exe).
; Built by the Release workflow:  iscc /DAppVersion=<version> packaging\windows\installer.iss
; Installs per user (no admin prompt) to %LOCALAPPDATA%\Programs\SteamDeckJewels. The library stays
; in %LOCALAPPDATA%\SteamDeckJewels, which updates and uninstalling leave alone.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6B0E7D52-8F4C-4C2A-9E53-1A7B9D3C5E21}
AppName=SteamDeck Jewels
AppVersion={#AppVersion}
AppVerName=SteamDeck Jewels {#AppVersion}
AppPublisher=scriptkittie
AppPublisherURL=https://github.com/scriptkittie/JewelLibrary
AppSupportURL=https://github.com/scriptkittie/JewelLibrary/issues
AppUpdatesURL=https://github.com/scriptkittie/JewelLibrary/releases
DefaultDirName={autopf}\SteamDeckJewels
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\release
OutputBaseFilename=SteamDeckJewels-Setup
SetupIconFile=..\..\assets\jewels\steamdeck-jewels-rainbow.ico
UninstallDisplayIcon={app}\SteamDeckJewels.exe
UninstallDisplayName=SteamDeck Jewels
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=force
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"

[InstallDelete]
; Replace the previous version's files cleanly.
Type: filesandordirs; Name: "{app}\_internal"
; Program files left by the old script-based installer. The library (data, assets\covers,
; .secrets, reports) in the same folder is kept.
Type: filesandordirs; Name: "{localappdata}\SteamDeckJewels\.venv"
Type: filesandordirs; Name: "{localappdata}\SteamDeckJewels\src"
Type: filesandordirs; Name: "{localappdata}\SteamDeckJewels\platform"
Type: filesandordirs; Name: "{localappdata}\SteamDeckJewels\tools"
Type: filesandordirs; Name: "{localappdata}\SteamDeckJewels\docs"
Type: filesandordirs; Name: "{localappdata}\SteamDeckJewels\assets\jewels"
Type: files; Name: "{localappdata}\SteamDeckJewels\requirements.txt"
Type: files; Name: "{localappdata}\SteamDeckJewels\update.log"
Type: files; Name: "{localappdata}\SteamDeckJewels\data\migrations.json"
Type: files; Name: "{userdesktop}\SteamDeck Jewels.lnk"
Type: files; Name: "{userdesktop}\SteamDeck Jewels Maintenance.lnk"

[Files]
Source: "..\..\dist\SteamDeckJewels\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\SteamDeck Jewels"; Filename: "{app}\SteamDeckJewels.exe"
Name: "{autodesktop}\SteamDeck Jewels"; Filename: "{app}\SteamDeckJewels.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SteamDeckJewels.exe"; Description: "Open SteamDeck Jewels"; Flags: nowait postinstall skipifsilent
; In-app updates run this installer silently with /RELAUNCH=1 so the app reopens by itself.
Filename: "{app}\SteamDeckJewels.exe"; Flags: nowait; Check: ShouldRelaunch

[Code]
function ShouldRelaunch: Boolean;
begin
  Result := WizardSilent and (ExpandConstant('{param:RELAUNCH|0}') = '1');
end;
