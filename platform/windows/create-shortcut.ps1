param([Parameter(Mandatory = $true)][string]$InstallDir)
$install = [System.IO.Path]::GetFullPath($InstallDir)
$launcher = Join-Path $install 'platform\windows\run.bat'
if (-not (Test-Path -LiteralPath $launcher)) { throw "Installed launcher not found: $launcher" }
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'SteamDeck Jewels.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $install
$shortcut.Description = 'SteamDeck Jewels game library'
$shortcut.IconLocation = (Join-Path $install 'assets\jewels\steamdeck-jewels-rainbow.ico')
$shortcut.Save()
Write-Host "Desktop shortcut created: $shortcutPath"

# Updates now happen inside the app (Help > Check for Updates), so the separate Maintenance
# shortcut from older versions is removed. The repair menu is still setup-windows.bat.
$maintenancePath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'SteamDeck Jewels Maintenance.lnk'
if (Test-Path -LiteralPath $maintenancePath) {
    Remove-Item -LiteralPath $maintenancePath
    Write-Host "Removed the old Maintenance shortcut; updates are now in Help > Check for Updates."
}
