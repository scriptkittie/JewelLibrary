#!/usr/bin/env python3
"""Command-line entry for updating an installed SteamDeck Jewels from GitHub.

The app does this itself from Help > Check for Updates. This wrapper lets the repair menu
(setup-windows.bat / platform/steamos/manager.sh) do the same when the app won't start.

    python tools/update_from_github.py --install <installed folder> [--check-only] [--pause]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from steamdeck_jewels.updater import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
