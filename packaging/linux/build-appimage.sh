#!/usr/bin/env bash
# Wraps the PyInstaller build in dist/SteamDeckJewels into release/SteamDeckJewels-x86_64.AppImage.
# Run from the repository root after `pyinstaller SteamDeckJewels.spec`, with PySide6 installed.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

APPDIR="build/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" release
cp -a dist/SteamDeckJewels/. "$APPDIR/usr/bin/"

python packaging/render_icon.py assets/jewels/steamdeck-jewels-rainbow.svg "$APPDIR/steamdeck-jewels.png"
cp "$APPDIR/steamdeck-jewels.png" "$APPDIR/.DirIcon"

cat > "$APPDIR/SteamDeckJewels.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=SteamDeck Jewels
Comment=Controller-friendly game library for SD-card collections
Exec=SteamDeckJewels
Icon=steamdeck-jewels
Terminal=false
Categories=Game;
DESKTOP

cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/SteamDeckJewels" "$@"
APPRUN
chmod +x "$APPDIR/AppRun" "$APPDIR/usr/bin/SteamDeckJewels"

TOOL="build/appimagetool-x86_64.AppImage"
if [ ! -x "$TOOL" ]; then
  curl -fsSL -o "$TOOL" \
    https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x "$TOOL"
fi
# Extract-and-run avoids needing FUSE on the build machine.
APPIMAGE_EXTRACT_AND_RUN=1 ARCH=x86_64 "$TOOL" --no-appstream "$APPDIR" release/SteamDeckJewels-x86_64.AppImage
echo "Built release/SteamDeckJewels-x86_64.AppImage"
