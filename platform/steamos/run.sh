#!/usr/bin/env bash
# Launches SteamDeck Jewels on SteamOS and other Linux desktops.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="$ROOT/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --upgrade pip
  "$VENV/bin/python" -m pip install -r "$ROOT/requirements.txt"
fi
export PYTHONPATH="$ROOT/src"
# Fullscreen on the Steam Deck; a normal resizable window on other Linux desktops.
if grep -qs '^ID="\?steamos' /etc/os-release; then
  exec "$VENV/bin/python" -m steamdeck_jewels "$@"
fi
exec "$VENV/bin/python" -m steamdeck_jewels --windowed "$@"
