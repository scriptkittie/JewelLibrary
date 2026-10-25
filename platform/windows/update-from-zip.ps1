param([Parameter(Mandatory = $true)][string]$InstallDir)

Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = 'Choose a SteamDeck Jewels Windows ZIP'
$dialog.Filter = 'ZIP archives (*.zip)|*.zip'
if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
    Write-Host 'No ZIP selected.'
    exit 1
}

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("SteamDeckJewelsUpdate-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempDir | Out-Null
try {
    Expand-Archive -LiteralPath $dialog.FileName -DestinationPath $tempDir -Force
    $setup = Get-ChildItem -LiteralPath $tempDir -Filter setup-windows.bat -File -Recurse | Select-Object -First 1
    if (-not $setup) { throw 'This is not a SteamDeck Jewels Windows ZIP.' }
    $env:SDJ_INSTALL = [System.IO.Path]::GetFullPath($InstallDir)
    & $setup.FullName update
    if ($LASTEXITCODE -ne 0) { throw "Setup exited with code $LASTEXITCODE." }
    Write-Host 'ZIP update completed successfully.'
}
finally {
    if (Test-Path -LiteralPath $tempDir) { Remove-Item -LiteralPath $tempDir -Recurse -Force }
}
