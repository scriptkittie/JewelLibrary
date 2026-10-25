# Linux setup

SteamDeck Jewels runs on most desktop Linux distributions with Python 3.10 or newer. The Linux download
uses the same scripts as the Steam Deck version, but opens in a normal window instead of fullscreen.

## Requirements

| Distribution | Install first |
|---|---|
| Ubuntu, Debian, Mint, Pop!_OS | `sudo apt install python3 python3-venv libxcb-cursor0` |
| Fedora | `sudo dnf install python3 xcb-util-cursor` |
| Arch, Manjaro, EndeavourOS | `sudo pacman -S python xcb-util-cursor` |

`libxcb-cursor0` / `xcb-util-cursor` is needed by Qt, the toolkit the app is built with. Without it the
app can install but fail to open its window.

## Install

1. Extract the Linux ZIP (or clone the repository) somewhere in your home folder.
2. Open a terminal in that folder and run:

   ```bash
   bash setup-linux.sh
   ```

3. Setup installs the app to `~/Applications/SteamDeckJewels`, creates a private Python environment
   (it downloads PySide6, so it needs internet the first time), and adds **SteamDeck Jewels** to your
   application menu and Desktop.

## SD cards

Jewel drives are matched by the card's volume label. The app looks where Linux desktops mount removable
media: `/run/media/<you>/<label>` (Fedora, Arch, SteamOS) and `/media/<you>/<label>` (Ubuntu, Debian).
Open the card in your file manager once so it is mounted, then use **Manage ▾ → Rescan Drives**.

## Updates and repair

The app checks for a new release every time it opens and asks whether to update. If it won't start,
run the repair menu:

```bash
bash ~/Applications/SteamDeckJewels/platform/steamos/manager.sh
```

## For developers

Building from source and running without installing are covered in [DEVELOPING.md](DEVELOPING.md).
