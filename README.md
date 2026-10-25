# SteamDeck Jewels

**A controller-friendly game library for collections spread across SD cards.**

Got more games than fit on one microSD card? SteamDeck Jewels gives each card a name and a gem (a
"jewel drive") and keeps one library of everything, with cover art, whether or not the card is plugged
in. It shows which cards are connected, tells you which card a game lives on, and launches the game when
its card is in. Built for the Steam Deck, and it also runs on Windows and desktop Linux.

## Features

- **One library for every card.** Games stay listed when their card is out, with the card's gem and
  status on each cover.
- **Made for the Deck.** A fullscreen interface that works with touch, the controller and a mouse. On
  Windows and Linux it opens in a normal window.
- **Cover art in a couple of clicks.** Search Steam and pick the right match from a list with
  thumbnails, or use a Steam AppID, a SteamGridDB link or your own 600×900 image. Change a cover any time
  from **Edit Game**.
- **Find things fast.** Search plus gem filters, however many cards you have.
- **NSFW protection.** Adult titles are hidden every time the app starts. The NSFW filter cycles
  **Hidden → Shown → Only**.
- **Keeps itself up to date.** Every time it opens it checks for a new version and asks whether you want
  to update.
- **Private.** Your games, covers, drive names and API key stay on your device.

## Download

Get the ZIP for your system from the [**Releases**](../../releases/latest) page:

| You have | Download |
|---|---|
| Steam Deck (SteamOS) | `SteamDeckJewels-SteamOS-<version>.zip` |
| Windows 10 or 11 | `SteamDeckJewels-Windows-<version>.zip` |
| Desktop Linux (Ubuntu, Fedora, Arch, …) | `SteamDeckJewels-Linux-<version>.zip` |

Each ZIP includes a `START_HERE.txt` with the same steps as below.

## Install

You only install once; after that the app updates itself. The first install needs an internet
connection to download the components the app runs on.

### Steam Deck / SteamOS

1. Switch to **Desktop Mode** and extract the SteamOS ZIP into `Downloads` (not onto the microSD card).
2. Open the extracted folder in Dolphin, right-click inside it and choose **Open Terminal Here**.
3. Type this and press Enter:

   ```bash
   bash setup-steamos.sh
   ```

4. When it says **Setup complete**, open **SteamDeck Jewels** from the Desktop or the application menu.
5. **To use it in Gaming Mode:** in Steam (Desktop Mode), choose **Games → Add a Non-Steam Game to My
   Library → Browse**, and select `~/Applications/SteamDeckJewels/platform/steamos/run.sh`. It opens
   fullscreen in Gaming Mode.

More detail: [Steam Deck setup guide](docs/STEAMOS_SETUP.md)

### Windows

1. Install [Python 3.10 or newer](https://www.python.org/downloads/). In the installer, keep **py
   launcher** ticked.
2. Extract the Windows ZIP (right-click → **Extract All**), then double-click `setup-windows.bat` in the
   extracted folder.
3. Type `1` (**Install / Update**) and press Enter.
4. When setup finishes, open **SteamDeck Jewels** from the new Desktop shortcut.

More detail: [Windows setup guide](docs/WINDOWS_SETUP.md)

### Linux

1. Install Python and one library the app's interface needs:
   - Ubuntu / Debian / Mint: `sudo apt install python3 python3-venv libxcb-cursor0`
   - Fedora: `sudo dnf install python3 xcb-util-cursor`
   - Arch: `sudo pacman -S python xcb-util-cursor`
2. Extract the Linux ZIP, open a terminal in the extracted folder and run:

   ```bash
   bash setup-linux.sh
   ```

3. Open **SteamDeck Jewels** from your application menu or Desktop.

More detail: [Linux setup guide](docs/LINUX_SETUP.md)

## Getting started

1. **Manage ▾ → Add Jewel Drive:** enter the volume name of an SD card and pick a gem for it.
2. **+ Add Game:** enter the game's name, choose its card and pick a cover.
3. **Click a game to launch it.** The first time, it asks you to find the game's program file (the
   `.exe` on Windows) and remembers it.

Everything else is in **Manage ▾** (Edit Game, Remove Game, Add Jewel Drive, Rescan Drives, Open SDJ
Folder) or by right-clicking a game. Removing a game from the library never deletes anything from the SD
card. The [first-run guide](docs/FIRST_RUN_GUIDE.md) walks through it all, including how to find a Steam
AppID.

### Good to know

- **Cards can move around.** When you pick a game's program from a connected card, SteamDeck Jewels
  remembers where it is *on the card*, so it keeps working if the card gets a different drive letter or
  you use it on another device.
- **Your own covers.** Besides the cover options in Add Game and Edit Game, you can drop an image into a
  game's cover folder yourself: **Manage ▾ → Open SDJ Folder**, then `assets/covers/<card>/<game>/`.
- **More cover sources (optional).** SteamGridDB has covers for games Steam doesn't. Add a free API key
  from **Help → Set Up SteamGridDB API Key**.
- **Many games at once.** If you're adding a large library, the cover tools can fetch covers in bulk.
  See your platform's setup guide.

## Updating

Every time SteamDeck Jewels opens, it checks for a new version. If there is one, it asks: **Update Now**
closes the app, installs the update and reopens it; **Not Now** leaves an **Update** button in the top
bar for later. You can also use **Help → Check for Updates** at any time. Updates keep your games,
drives, covers and API key.

## Troubleshooting

- **Windows says "Windows protected your PC" when I run setup.** That's Windows SmartScreen being
  cautious about downloaded scripts. Click **More info → Run anyway**.
- **"Python 3 was not found."** Install Python from [python.org](https://www.python.org/downloads/)
  (Windows: keep **py launcher** ticked), then run setup again.
- **A game says Offline.** Insert its card, wait for your computer or Deck to show it, then use
  **Manage ▾ → Rescan Drives**. The card's volume name must match the one you gave the jewel drive.
- **The app won't open after an update or a crash.** Run setup again from the ZIP you downloaded. It
  repairs the installation without touching your library.
- **On Linux the app installs but doesn't open.** Make sure the library from step 1 of the Linux install
  is installed.

## Backing up and uninstalling

Your library lives in the app's folder:

- **Windows:** `%LOCALAPPDATA%\SteamDeckJewels` (paste that into File Explorer's address bar)
- **Steam Deck and Linux:** `~/Applications/SteamDeckJewels`

To **back up** your library, copy the `data` and `assets/covers` folders from there.

To **uninstall**, delete that folder and the SteamDeck Jewels shortcut. On Steam Deck and Linux, also
delete `~/.local/share/applications/SteamDeckJewels.desktop`. This removes your library too, so back it
up first if you want to keep it.

## Privacy

SteamDeck Jewels starts with an empty library and stores everything on your device. It only goes online
to look up covers when you ask it to, and to check this page for new versions.

## License and credits

MIT licensed. See [LICENSE](LICENSE).

SteamDeck Jewels is a fan-made project and isn't affiliated with or endorsed by Valve. Steam and Steam
Deck are trademarks of Valve Corporation.
