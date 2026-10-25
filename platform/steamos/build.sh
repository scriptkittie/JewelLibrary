#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python3 -m venv .build-venv
.build-venv/bin/python -m pip install --upgrade pip
.build-venv/bin/python -m pip install -r requirements.txt pyinstaller

rm -rf build dist
.build-venv/bin/pyinstaller \
  --noconfirm \
  --windowed \
  --name SteamDeckJewels \
  --add-data "data:data" \
  --add-data "assets:assets" \
  src/steamdeck_jewels/app.py

echo
echo "Built Linux application at:"
echo "  dist/SteamDeckJewels/SteamDeckJewels"
echo
echo "This folder build is directly runnable on SteamOS."
echo "For a single-file AppImage, bundle this folder with appimagetool/AppImage tooling."
