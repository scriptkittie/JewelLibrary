#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  echo "Run setup-steamos.sh first so the Python environment exists."
  exit 1
fi
"$ROOT/.venv/bin/python" "$ROOT/tools/covers/resolve_unresolved.py"
