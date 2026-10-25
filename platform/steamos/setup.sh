#!/usr/bin/env bash
set -euo pipefail

SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODE="${1:-update}"
INSTALL="${SDJ_INSTALL:-$HOME/Applications/SteamDeckJewels}"
VENV="$INSTALL/.venv"
APPLICATIONS="$HOME/.local/share/applications"
if command -v xdg-user-dir >/dev/null 2>&1; then
  DESKTOP="$(xdg-user-dir DESKTOP)"
fi
DESKTOP="${DESKTOP:-$HOME/Desktop}"
APP_ENTRY="$APPLICATIONS/SteamDeckJewels.desktop"
DESKTOP_ENTRY="$DESKTOP/SteamDeckJewels.desktop"
MAINTENANCE_ENTRY="$APPLICATIONS/SteamDeckJewelsMaintenance.desktop"
MAINTENANCE_DESKTOP="$DESKTOP/SteamDeckJewelsMaintenance.desktop"

setup_failed() {
  local status=$?
  echo
  echo "Setup did not finish (error $status)."
  echo "The Konsole starting-folder warning is unrelated to this installer."
  echo "Keep this window open and use the last error above to diagnose the problem."
  if [ -t 0 ]; then
    read -r -p "Press Enter to close..." _ || true
  fi
  exit "$status"
}
trap setup_failed ERR

echo "Installing SteamDeck Jewels to $INSTALL..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required but was not found."
  echo "Install Python 3 (on the Steam Deck, from Desktop Mode), then run this setup again."
  exit 1
fi
SAME_FOLDER=0
if [ -d "$INSTALL" ] && [ "$(cd "$INSTALL" && pwd -P)" = "$(cd "$SOURCE" && pwd -P)" ]; then
  SAME_FOLDER=1
  echo "Running from the installed copy, so there are no new files to copy."
  echo "To update the app itself, run setup-steamos.sh from the downloaded or cloned folder."
  echo "Refreshing the Python environment and shortcuts instead..."
fi
if [ "$SAME_FOLDER" -eq 0 ]; then
mkdir -p "$INSTALL/src" "$INSTALL/tools" "$INSTALL/docs" "$INSTALL/platform/steamos" "$INSTALL/assets" "$INSTALL/data" "$APPLICATIONS" "$DESKTOP"
cp -a "$SOURCE/src/." "$INSTALL/src/"
cp -a "$SOURCE/tools/." "$INSTALL/tools/"
cp -a "$SOURCE/docs/." "$INSTALL/docs/"
cp "$SOURCE/requirements.txt" "$INSTALL/requirements.txt"
cp "$SOURCE/platform/steamos/run.sh" "$INSTALL/platform/steamos/run.sh"
cp "$SOURCE/platform/steamos/setup.sh" "$INSTALL/platform/steamos/setup.sh"
cp "$SOURCE/platform/steamos/manager.sh" "$INSTALL/platform/steamos/manager.sh"
cp "$SOURCE/platform/steamos/fetch-covers.sh" "$INSTALL/platform/steamos/fetch-covers.sh"
cp "$SOURCE/platform/steamos/resolve-covers.sh" "$INSTALL/platform/steamos/resolve-covers.sh"
# The library files (data/drives.json, data/games.json) are created by the app on first launch
# and are never overwritten by setup.
cp -an "$SOURCE/assets/." "$INSTALL/assets/"
if [ ! -d "$INSTALL/reports" ]; then
  cp -a "$SOURCE/reports" "$INSTALL/reports"
fi
fi
if [ ! -x "$VENV/bin/python" ]; then
  if ! python3 -m venv "$VENV"; then
    echo
    echo "SteamOS could not create the private Python environment."
    echo "Install Python's venv support (Debian/Ubuntu: sudo apt install python3-venv), then run setup again."
    exit 1
  fi
fi
"$VENV/bin/python" -m pip install --upgrade pip
if [ "$MODE" = "repair" ]; then
  "$VENV/bin/python" -m pip install --force-reinstall -r "$INSTALL/requirements.txt"
else
  "$VENV/bin/python" -m pip install -r "$INSTALL/requirements.txt"
fi
"$VENV/bin/python" -c 'import PySide6' || {
  echo "PySide6 installed but could not be imported."
  exit 1
}

chmod +x "$INSTALL/platform/steamos/"*.sh

write_entry() {
  local destination="$1"
  printf '%s\n' \
    '[Desktop Entry]' \
    'Type=Application' \
    'Name=SteamDeck Jewels' \
    'Comment=Controller-friendly jewel drive game library' \
    "Exec=\"$INSTALL/platform/steamos/run.sh\"" \
    "Icon=$INSTALL/assets/jewels/steamdeck-jewels-rainbow.svg" \
    'Terminal=false' \
    'Categories=Game;' \
    'StartupNotify=true' > "$destination"
  chmod +x "$destination"
}

write_entry "$APP_ENTRY"
write_entry "$DESKTOP_ENTRY"

# Updates now happen inside the app (Help > Check for Updates), so remove the separate
# Maintenance launcher from older versions. The repair menu is still platform/steamos/manager.sh.
rm -f "$MAINTENANCE_ENTRY" "$MAINTENANCE_DESKTOP"
command -v gio >/dev/null 2>&1 && gio set "$DESKTOP_ENTRY" metadata::trusted true || true
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPLICATIONS" || true

echo
echo "Setup complete."
echo "Desktop shortcut: $DESKTOP_ENTRY"
echo "Application menu:  $APP_ENTRY"
echo "Install location:  $INSTALL"
echo "To launch it now:   $INSTALL/platform/steamos/run.sh"
echo "You can also add $INSTALL/platform/steamos/run.sh to Steam as a Non-Steam Game."
