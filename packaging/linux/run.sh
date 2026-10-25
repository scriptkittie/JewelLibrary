#!/usr/bin/env bash
# Run SteamDeck Jewels from the source code (for development). Uses the repository's data/ folder.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="$ROOT/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install -r "$ROOT/requirements.txt"
fi
PYTHONPATH="$ROOT/src" exec "$VENV/bin/python" -m steamdeck_jewels "$@"
