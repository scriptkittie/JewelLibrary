# SteamOS setup

1. Switch to Desktop Mode.
2. Extract the SteamOS ZIP (or clone the repository) into your home folder, for example `~/Downloads`.
   Don't run it from the microSD card: exFAT cards drop Linux file permissions.
3. Open the extracted folder in Dolphin, right-click inside it and choose **Open Terminal Here**.
4. Run:

   ```bash
   bash setup-steamos.sh
   ```

5. Setup installs the app to `~/Applications/SteamDeckJewels` and creates a private Python environment
   there. It does not change SteamOS system packages. The first setup needs internet to download
   PySide6.
6. Open **SteamDeck Jewels** from the Desktop shortcut or the application menu. No terminal is needed
   after setup.
7. For Gaming Mode, add `~/Applications/SteamDeckJewels/platform/steamos/run.sh` to Steam as a
   Non-Steam Game. It opens fullscreen.

Always start setup with `bash setup-steamos.sh`. Double-clicking a `.sh` file doesn't run it the way
a Windows `.bat` file runs.

## Updates and repair

The app updates itself. Every time it opens it checks for a new release and asks whether to update;
**Update Now** closes it, installs the update and reopens it. **Not Now** leaves an Update button in the
top bar, and **Help → Check for Updates** works at any time. Updates keep your `data/`
library, covers and `.secrets/` SteamGridDB key. Updating from Desktop Mode is recommended.

If the app won't start, open a terminal and run the repair menu:

```bash
bash ~/Applications/SteamDeckJewels/platform/steamos/manager.sh
```

It can check the installation, update from GitHub or a downloaded ZIP, and repair the Python
environment and shortcuts.

## Cover tools

From the installed folder:

```bash
~/Applications/SteamDeckJewels/platform/steamos/fetch-covers.sh     # automatic Steam/SteamGridDB pass
~/Applications/SteamDeckJewels/platform/steamos/resolve-covers.sh   # interactive review of what the automatic pass missed
```

Results are written to `~/Applications/SteamDeckJewels/reports/`.

## Troubleshooting

If Konsole says it could not find a folder such as `/home/deck/desktop/deck` and starts `bash` instead,
that is a stale Konsole profile setting, not an installer error. To remove the warning, open
**Settings > Edit Current Profile > General** and set **Initial directory** to `/home/deck`.

## For developers

- `bash run-steamos.sh` runs the app straight from the repository (using its own `data/` folder).
- `bash build-steamos.sh` builds a standalone PyInstaller folder at `dist/SteamDeckJewels/`.
