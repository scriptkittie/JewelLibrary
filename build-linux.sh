#!/usr/bin/env bash
# Linux uses the same scripts as SteamOS.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$ROOT/platform/steamos/build.sh" "$@"
