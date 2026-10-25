# Release checklist

Run through this before tagging a release. Test with the packaged ZIPs
(`python tools/package_release.py`), not the repository folder.

## Windows

- [ ] Extract the Windows ZIP and double-click `setup-windows.bat`.
- [ ] Choose **Install / Update from this download** and confirm it finishes without errors.
- [ ] Confirm the installation path is `%LOCALAPPDATA%\SteamDeckJewels`.
- [ ] Launch **SteamDeck Jewels** from the Desktop shortcut; a fresh install shows the welcome message.
- [ ] **Manage ▾ → Add Jewel Drive**, then **+ Add Game** with **Search Steam by game name**; confirm the
      results list appears and the chosen cover is saved.
- [ ] Confirm the NSFW filter starts on **Hidden** and cycles **Shown → Only → Hidden**.
- [ ] **Manage ▾ → Edit Game**: replace a cover; the old one moves to `_replaced`.
- [ ] Resize and maximize the window; the grid reflows with no column hidden behind the scrollbar.
- [ ] Add enough jewel drives to overflow the filter row; it scrolls and shows faded edges.
- [ ] **Manage ▾ → Rescan Drives** and **Open SDJ Folder** work.
- [ ] Run setup again (update); confirm drives, games and covers are kept.

## SteamOS / Steam Deck

- [ ] In Desktop Mode, extract the SteamOS ZIP into `~/Downloads`.
- [ ] Run `bash setup-steamos.sh` and confirm it ends with "Setup complete."
- [ ] Confirm installation at `~/Applications/SteamDeckJewels`.
- [ ] Launch from the Desktop shortcut; repeat the in-app checks above (touch scrolling included).
- [ ] Add `~/Applications/SteamDeckJewels/platform/steamos/run.sh` to Steam as a Non-Steam Game.
- [ ] In Gaming Mode, confirm the app opens fullscreen and the controller can reach every button.
- [ ] Insert a jewel SD card and confirm its drive shows as connected after **Rescan Drives**.

## Linux (Ubuntu or Fedora)

- [ ] Install the requirements from `docs/LINUX_SETUP.md`, extract the Linux ZIP and run
      `bash setup-linux.sh`.
- [ ] Launch from the application menu; the app opens in a normal window with the jewel icon.
- [ ] Mount an SD card and confirm its jewel shows as connected after **Rescan Drives**.

## Packaging

- [ ] Bump the version in `src/steamdeck_jewels/__init__.py` and `pyproject.toml`.
- [ ] Confirm neither ZIP contains `.secrets`, `data/*.json`, personal covers or `__pycache__`.
- [ ] Push a `v<version>` tag; the Release workflow publishes both ZIPs.
- [ ] On an older install, confirm the update prompt appears on launch and updating reopens the app with the
      "Update complete" message.
