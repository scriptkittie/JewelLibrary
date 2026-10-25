#!/usr/bin/env bash
# Build the Linux app with PyInstaller and wrap it as release/SteamDeckJewels-x86_64.AppImage.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
python3 -m venv .build-venv
.build-venv/bin/python -m pip install -r requirements.txt pyinstaller
.build-venv/bin/pyinstaller --noconfirm --clean SteamDeckJewels.spec
PATH="$ROOT/.build-venv/bin:$PATH" bash packaging/linux/build-appimage.sh
