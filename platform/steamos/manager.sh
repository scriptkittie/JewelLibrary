#!/usr/bin/env bash
set -u

INSTALL="${SDJ_INSTALL:-$HOME/Applications/SteamDeckJewels}"
SELF_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

pause_menu() {
  echo
  read -r -p "Press Enter to continue..." _
}

check_install() {
  echo
  local missing=0
  for item in \
    "src/steamdeck_jewels/app.py:Application source" \
    "assets/covers:Cover library" \
    ".venv/bin/python:Python environment" \
    "platform/steamos/run.sh:Application launcher"; do
    local path="${item%%:*}" label="${item#*:}"
    if [ -e "$INSTALL/$path" ]; then
      echo "[OK] $label"
    else
      echo "[MISSING] $label"
      missing=1
    fi
  done
  if [ -e "$INSTALL/data/games.json" ]; then
    echo "[OK] Game database"
  else
    echo "[INFO] Game database is created the first time you open SteamDeck Jewels"
  fi
  if [ "$missing" -eq 0 ]; then
    echo "Installation looks healthy."
  else
    echo "Use Repair to restore missing application files."
  fi
}

choose_zip() {
  if command -v kdialog >/dev/null 2>&1; then
    kdialog --getopenfilename "$HOME" '*.zip|ZIP archives' 2>/dev/null || true
  elif command -v zenity >/dev/null 2>&1; then
    zenity --file-selection --file-filter='ZIP archives | *.zip' 2>/dev/null || true
  else
    read -r -p "Full path to update ZIP: " zip_path
    printf '%s\n' "$zip_path"
  fi
}

update_from_zip() {
  local zip_path temp_dir setup_path
  zip_path="$(choose_zip)"
  [ -n "$zip_path" ] || { echo "No ZIP selected."; return 1; }
  [ -f "$zip_path" ] || { echo "ZIP not found: $zip_path"; return 1; }
  temp_dir="$(mktemp -d)" || return 1
  if ! ZIP_PATH="$zip_path" DEST_PATH="$temp_dir" python3 -c \
    'import os, zipfile; zipfile.ZipFile(os.environ["ZIP_PATH"]).extractall(os.environ["DEST_PATH"])'; then
    echo "Could not extract that ZIP."
    rm -rf -- "$temp_dir"
    return 1
  fi
  setup_path="$(find "$temp_dir" -type f -name setup-steamos.sh -print -quit)"
  if [ -z "$setup_path" ]; then
    echo "This is not a SteamDeck Jewels SteamOS or Linux ZIP."
    rm -rf -- "$temp_dir"
    return 1
  fi
  bash "$setup_path" update
  local status=$?
  rm -rf -- "$temp_dir"
  return "$status"
}

update_from_github() {
  # The update replaces this menu's own file, so hand over to the updater instead of returning.
  local python="$INSTALL/.venv/bin/python"
  [ -x "$python" ] || python="python3"
  exec "$python" "$SELF_ROOT/tools/update_from_github.py" --install "$INSTALL" --pause
}

while true; do
  clear
  echo "========================================"
  echo "    SteamDeck Jewels Maintenance"
  echo "========================================"
  echo "Install location: $INSTALL"
  echo
  echo "  1. Check installation"
  echo "  2. Update from GitHub (latest release)"
  echo "  3. Update from a ZIP"
  echo "  4. Repair installation"
  echo "  5. Launch SteamDeck Jewels"
  echo "  6. Open SDJ folder"
  echo "  7. Install / update from this folder"
  echo "  8. Exit"
  echo
  read -r -p "Choose an option [1-8]: " choice
  case "$choice" in
    1) check_install; pause_menu ;;
    2) update_from_github ;;
    3) update_from_zip; pause_menu ;;
    4) bash "$SELF_ROOT/platform/steamos/setup.sh" repair; pause_menu ;;
    5) "$INSTALL/platform/steamos/run.sh" & exit 0 ;;
    6) xdg-open "$INSTALL" >/dev/null 2>&1 & ;;
    7) bash "$SELF_ROOT/platform/steamos/setup.sh" update; pause_menu ;;
    8) exit 0 ;;
    *) echo "Invalid choice."; pause_menu ;;
  esac
done
