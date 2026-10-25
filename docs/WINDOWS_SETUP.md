# Windows setup

You need Python 3.10 or newer from python.org, installed with the **py launcher** option.

Double-click `setup-windows.bat` and choose **1. Install / Update**. It:

1. Copies the application to `%LOCALAPPDATA%\SteamDeckJewels`.
2. Creates a private Python environment there and installs PySide6 (needs internet the first time).
3. Creates a **SteamDeck Jewels** shortcut on your Desktop.

Your library (`data\drives.json`, `data\games.json`), covers and SteamGridDB key live in the installed
folder. Setup never overwrites them, so running it again is a safe way to update.

## Updates and repair

The app updates itself. Every time it opens it checks for a new release and asks whether to update;
**Update Now** closes it, installs the update and reopens it. **Not Now** leaves an Update button in the
top bar, and **Help → Check for Updates** works at any time.

If the app won't start, double-click `setup-windows.bat` again (from the download, or from
`%LOCALAPPDATA%\SteamDeckJewels\platform\windows\manager.bat`). Its menu can check the installation,
update from GitHub or a downloaded ZIP, and repair the Python environment and shortcuts.

No command window stays open while the app runs; one appears only while setup or repair is working.
