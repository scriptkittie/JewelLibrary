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

| You have | Download |
|---|---|
| **Windows 10 or 11** | [**SteamDeckJewels-Setup.exe**](https://github.com/scriptkittie/JewelLibrary/releases/latest/download/SteamDeckJewels-Setup.exe) |
| **Steam Deck** or **desktop Linux** | [**SteamDeckJewels-x86_64.AppImage**](https://github.com/scriptkittie/JewelLibrary/releases/latest/download/SteamDeckJewels-x86_64.AppImage) |

These always link to the newest version. Older versions are on the [Releases](../../releases) page.

## Install

### Windows

1. Download **SteamDeckJewels-Setup.exe** and open it.
2. If Windows shows **"Windows protected your PC"**, click **More info → Run anyway**. (It appears
   because this free app isn't code-signed.)
3. Click **Install**. SteamDeck Jewels opens when it's done, and you'll find it in the Start menu and on
   your Desktop.

### Steam Deck

1. Switch to **Desktop Mode** (hold the power button → **Switch to Desktop**).
2. Download **SteamDeckJewels-x86_64.AppImage** with the browser.
3. In the **Dolphin** file manager, move it somewhere it can stay, such as your home folder. (Not the
   microSD card.)
4. Right-click it → **Properties → Permissions**, tick **Is executable**, and click **OK**.
5. Double-click it to open SteamDeck Jewels. It also adds itself to the application menu.
6. **To use it in Gaming Mode:** open Steam in Desktop Mode, choose **Games → Add a Non-Steam Game to
   My Library → Browse**, change the file type to **All Files**, pick the AppImage, and click **Add
   Selected Programs**. In Gaming Mode it opens fullscreen.

### Linux

1. Download **SteamDeckJewels-x86_64.AppImage**.
2. Make it executable: right-click → **Properties → Permissions → Allow executing as program**, or run
   `chmod +x SteamDeckJewels-x86_64.AppImage`.
3. Double-click it to open. It adds itself to your application menu.

If it doesn't open, your system may need FUSE 2, which AppImages use:
Ubuntu 24.04 and newer `sudo apt install libfuse2t64`, older Ubuntu/Debian `sudo apt install libfuse2`,
Fedora `sudo dnf install fuse-libs`, Arch `sudo pacman -S fuse2`.

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

## Updating

Every time SteamDeck Jewels opens, it checks for a new version. If there is one, it asks: **Update Now**
downloads it, installs it and reopens the app; **Not Now** leaves an **Update** button in the top bar for
later. You can also use **Help → Check for Updates** at any time. Your games, drives, covers and API key
are never touched by updates.

## Troubleshooting

- **"Windows protected your PC" when installing.** Click **More info → Run anyway**.
- **The AppImage won't open.** Make sure it's marked executable (step 4 / step 2 above). On Linux, install
  FUSE 2 as shown above.
- **A game says Offline.** Insert its card, wait for your computer or Deck to show it, then use
  **Manage ▾ → Rescan Drives**. The card's volume name must match the one you gave the jewel drive.
- **An update didn't finish.** Download the latest version from the links above and install or replace
  it. Your library is kept.
- **I moved the AppImage and Steam can't find it.** Add it to Steam again from its new location.

## Your library, backups and uninstalling

Your library is stored separately from the app, so reinstalling or updating never loses it:

- **Windows:** `%LOCALAPPDATA%\SteamDeckJewels` (paste that into File Explorer's address bar)
- **Steam Deck and Linux:** `~/.local/share/SteamDeckJewels`

**Manage ▾ → Open SDJ Folder** opens it. To back up your library, copy that whole folder.

**To uninstall on Windows,** use **Settings → Apps → Installed apps → SteamDeck Jewels → Uninstall**. **On
Steam Deck and Linux,** delete the AppImage and `~/.local/share/applications/SteamDeckJewels.desktop`.
Your library folder stays in both cases; delete it too if you want to remove everything.

## Privacy

SteamDeck Jewels starts with an empty library and stores everything on your device. It only goes online
to look up covers when you ask it to, and to check this page for new versions.

## License

MIT licensed. See [LICENSE](LICENSE).

SteamDeck Jewels is a fan-made project and isn't affiliated with or endorsed by Valve. Steam and Steam
Deck are trademarks of Valve Corporation.
