# SteamDeck Jewels

**A controller-friendly game library for collections spread across SD cards.**

Got more games than fit on one microSD card? SteamDeck Jewels gives each card a name and a gem (a
"jewel drive") and keeps one library of everything, with cover art, whether or not the card is plugged
in. It shows which cards are connected, tells you which card a game lives on, and launches the game when
its card is in. Built for the Steam Deck, and it also runs on Windows and desktop Linux.

## Features

- **One library for every card.** Games stay listed when their card is out, with the card's gem and
  status on each cover.
- **Made for the Deck.** A fullscreen 1280×800 interface that works with touch, the controller and a
  mouse. It also runs in a normal window on Windows and Linux.
- **Cover art in a couple of clicks.** Search Steam and pick the right match from a list with
  thumbnails, or use a Steam AppID, a SteamGridDB link or your own 600×900 image. Change a cover any time
  from **Edit Game**.
- **Find things fast.** Search plus gem filters. The filter row scrolls, so it handles any number of
  cards.
- **NSFW protection.** Adult titles are hidden every time the app starts. The NSFW filter cycles
  **Hidden → Shown → Only**.
- **Keeps itself up to date.** Every time it opens it checks for a new release and asks whether you want
  to update. Your library is never touched by updates.
- **Private by design.** Your games, covers, drive names and API key stay on your device.

## Download

Get the ZIP for your system from the [**Releases**](../../releases/latest) page:

| You have | Download | Then |
|---|---|---|
| Steam Deck (SteamOS) | `SteamDeckJewels-SteamOS-<version>.zip` | [SteamOS setup](#steam-deck--steamos) |
| Windows 10/11 | `SteamDeckJewels-Windows-<version>.zip` | [Windows setup](#windows) |
| Desktop Linux | `SteamDeckJewels-Linux-<version>.zip` | [Linux setup](#linux) |

Each ZIP includes `START_HERE.txt` with the same steps.

## Install

Setup copies the app to a private folder, creates its own Python environment (it downloads PySide6, so
it needs internet the first time) and adds a shortcut. You only do this once; after that the app updates
itself.

### Steam Deck / SteamOS

1. Switch to **Desktop Mode** and extract the SteamOS ZIP into `Downloads` (not onto the microSD card).
2. Open the extracted folder in Dolphin, right-click inside it and choose **Open Terminal Here**.
3. Run:

   ```bash
   bash setup-steamos.sh
   ```

4. Open **SteamDeck Jewels** from the Desktop or the application menu.
5. For Gaming Mode, add `~/Applications/SteamDeckJewels/platform/steamos/run.sh` to Steam as a
   **Non-Steam Game**. It opens fullscreen there.

More detail: [docs/STEAMOS_SETUP.md](docs/STEAMOS_SETUP.md)

### Windows

1. Install [Python 3.10 or newer](https://www.python.org/downloads/) with the **py launcher** option.
2. Extract the Windows ZIP, then double-click `setup-windows.bat`.
3. Type `1` (**Install / Update**) and press Enter.
4. Open **SteamDeck Jewels** from the new Desktop shortcut.

The app installs to `%LOCALAPPDATA%\SteamDeckJewels`. More detail:
[docs/WINDOWS_SETUP.md](docs/WINDOWS_SETUP.md)

### Linux

1. Install Python and Qt's one extra library:
   - Ubuntu / Debian / Mint: `sudo apt install python3 python3-venv libxcb-cursor0`
   - Fedora: `sudo dnf install python3 xcb-util-cursor`
   - Arch: `sudo pacman -S python xcb-util-cursor`
2. Extract the Linux ZIP, open a terminal in the extracted folder and run:

   ```bash
   bash setup-linux.sh
   ```

3. Open **SteamDeck Jewels** from your application menu or Desktop.

The app installs to `~/Applications/SteamDeckJewels`. More detail: [docs/LINUX_SETUP.md](docs/LINUX_SETUP.md)

## Getting started

1. **Manage ▾ → Add Jewel Drive**: enter the volume name of an SD card and pick a gem.
2. **+ Add Game**: enter the game, choose its card, and pick a cover.
3. Click a game to launch it. The first time, it asks for the game's `.exe` (or program) and remembers
   it.

Everything else lives in **Manage ▾** (Edit Game, Remove Game, Add Jewel Drive, Rescan Drives, Open SDJ
Folder) or by right-clicking a game. Removing a game never deletes anything from the SD card. The
[first-run guide](docs/FIRST_RUN_GUIDE.md) covers it all, including finding a Steam AppID.

### Tips

- **Covers** live in `assets/covers/<Jewel>/<Game>/` inside the app's folder (NSFW titles under
  `<Jewel>/NSFW/<Game>/`). You can also drop an image in by hand. Replaced covers are moved to a
  `_replaced` subfolder, not deleted.
- **Portable launch paths:** a path starting with `{drive}` becomes the card's location when it's
  connected (`E:\` on Windows, `/run/media/...` or `/media/...` on Linux), so the same entry works on every
  machine:

  ```json
  "target": "{drive}Games/My Game/MyGame.exe"
  ```

- **SteamGridDB (optional):** adds covers Steam doesn't have. Add a free API key from **Help → Set Up
  SteamGridDB API Key**. It's stored only on your device.
- **Lots of covers at once:** `fetch-covers` does an automatic pass and `resolve-covers` walks you through
  what's left (`.bat` on Windows, `platform/steamos/*.sh` on Linux and SteamOS).

## Updating

Every time SteamDeck Jewels opens, it checks for a new release. If there is one, it asks: **Update Now**
closes the app, installs the update and reopens it; **Not Now** leaves an Update button in the top bar.
You can also use **Help → Check for Updates** at any time. Updates keep your games, drives, covers and
API key.

If the app ever won't start, run setup again from the download (or the repair menu in the installed
folder) to check and repair it.

## Building from source

```text
assets/        gem icons, placeholder cover (your covers are git-ignored)
data/          your drives.json and games.json, created on first run (git-ignored)
docs/          setup guides and the release checklist
platform/      setup, run, build and repair scripts (windows/, steamos/ for SteamOS and Linux)
src/           the application (steamdeck_jewels package, Python + PySide6)
tools/         cover tools, gem generator, release packager, updater
```

- **Run without installing:** `run-windows.bat`, `bash run-linux.sh` or `bash run-steamos.sh`.
- **Standalone build (PyInstaller):** `build-windows.bat` or `bash build-linux.sh`. Output goes to
  `dist/SteamDeckJewels/`.
- **Release ZIPs:** `python tools/package_release.py` writes the Windows, SteamOS and Linux ZIPs to
  `release/`.
- **Publishing a release:** bump the version in `src/steamdeck_jewels/__init__.py` and `pyproject.toml`,
  then push a tag such as `v0.3.1`. The Release workflow builds all three ZIPs and publishes them on the
  Releases page, and installed copies offer the update the next time they open. The repository the app
  checks is `GITHUB_REPO` in `src/steamdeck_jewels/updater.py`.

Before a release, run through [docs/CHECKLIST.md](docs/CHECKLIST.md).

## Privacy

Releases start with an empty library. Your drives, games, launch paths, covers and API key stay on your
device. `.gitignore` keeps them out of the repository and the release packager never includes them. The
only network requests are Steam/SteamGridDB cover lookups you start, and the update check against this
repository's GitHub Releases.

## License

MIT. See [LICENSE](LICENSE).

SteamDeck Jewels is a fan-made project and isn't affiliated with or endorsed by Valve. Steam and Steam
Deck are trademarks of Valve Corporation.
