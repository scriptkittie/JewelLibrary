# Developing SteamDeck Jewels

Notes for building, running from source and publishing releases. If you just want to use the app, the
[README](../README.md) has everything you need.

## Project layout

```text
assets/        gem icons and the placeholder cover (personal covers are git-ignored)
data/          drives.json and games.json, created on first run (git-ignored)
docs/          user setup guides, this file and the release checklist
platform/      setup, run, build and repair scripts: windows/, and steamos/ (used for SteamOS and Linux)
src/           the application: steamdeck_jewels package (Python 3.10+, PySide6)
tools/         cover tools, gem-icon generator, release packager, command-line updater
```

The app is `src/steamdeck_jewels/app.py`; self-updating lives in `src/steamdeck_jewels/updater.py`.

## Run from source

| Windows | SteamOS | Linux |
|---|---|---|
| `run-windows.bat` | `bash run-steamos.sh` | `bash run-linux.sh` |

The first run creates a `.venv` in the repository and installs PySide6. Running from source uses the
repository's own `data/` folder, not an installed copy's library, and the in-app updater is disabled for
a git checkout (`git pull` instead).

## Standalone builds

`build-windows.bat` or `bash build-linux.sh` / `bash build-steamos.sh` build a PyInstaller folder at
`dist/SteamDeckJewels/`. Standalone builds don't self-update; users download new ones from Releases.

## Releases

1. Bump the version in `src/steamdeck_jewels/__init__.py` and `pyproject.toml`.
2. Run through [CHECKLIST.md](CHECKLIST.md). `python tools/package_release.py` builds the three ZIPs into
   `release/` locally for testing.
3. Commit, push, then tag the commit `v<version>` (for example `v0.3.1`) and push the tag.
4. `.github/workflows/release.yml` builds the Windows, SteamOS and Linux ZIPs and publishes a GitHub
   release. Edit its notes on GitHub if you like.
5. Installed copies see the new release the next time they open and offer to update. They check the
   repository named by `GITHUB_REPO` in `src/steamdeck_jewels/updater.py`, which must be public.

The packager only includes release files, so personal libraries, covers, API keys and virtual
environments never ship. `.gitattributes` keeps `.sh` files LF and `.bat`/`.ps1` files CRLF.

## How updating works

The app checks `api.github.com/repos/<GITHUB_REPO>/releases/latest` at startup in the background. If
the tag is newer than the installed `__version__`, it asks the user. On **Update Now** it starts
`python -m steamdeck_jewels.updater --install <folder> --wait-pid <pid> --relaunch` and quits. The
updater waits for the app to exit, downloads the platform's ZIP, runs its setup script in update mode
(`SDJ_NONINTERACTIVE=1`, output in `update.log`), writes `.update-status.json` and relaunches the app,
which then shows the result.

## Repair menu

`setup-windows.bat` (Windows) and `platform/steamos/manager.sh` (SteamOS/Linux) open a text menu to
install/update from a folder, update from GitHub or a ZIP, repair the Python environment and check the
installation. It's the fallback for when the app itself won't start.

## Utilities

- `tools/generate_jewels.py` regenerates the gem SVGs.
- `tools/covers/fetch_covers.py` and `resolve_unresolved.py` fill in missing covers in bulk
  (wrapped by `fetch-covers.bat` / `resolve-covers.bat` and `platform/steamos/*-covers.sh`).
