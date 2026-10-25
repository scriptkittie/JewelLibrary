# First-run guide

SteamDeck Jewels (SDJ) installs with an empty library. No API keys, game lists, drive names, launch
paths or covers are included.

## 1. Add your first jewel drive

Open SDJ and choose **Manage ▾ → Add Jewel Drive**. Enter the volume name printed on your SD card, then
choose the gem you want for it. If you do not use removable cards, a jewel also works as a simple
category for organizing games.

## 2. Add a game

Choose **+ Add Game**, enter the game name and select its jewel drive. For the cover, the easiest choice
is **Search Steam by game name**: SDJ shows Steam's matches with thumbnails and AppIDs so you can pick the
right one. You can instead enter a Steam AppID, a direct SteamGridDB image URL, or a local 600×900 image.

Tick **NSFW** for adult titles. They are hidden every time SDJ starts; the **NSFW** filter button cycles
between **Hidden**, **Shown** and **Only**.

## 3. Change things later

**Manage ▾ → Edit Game** (or right-click a game card) changes a game's name, drive, NSFW setting,
executable or cover. **Manage ▾ → Remove Game** removes an entry, optionally with its cover folder. It
never deletes anything from the SD card.

## Finding a Steam AppID

Open the game's page in the Steam Store and look at the address. For example:

```text
https://store.steampowered.com/app/105600/Terraria/
```

The number immediately after `/app/` is the AppID, here `105600`. Enter only the number.

## Optional SteamGridDB API key

SteamGridDB can supply artwork when Steam has no suitable 600×900 cover.

1. Create or sign in to an account at `https://www.steamgriddb.com/`.
2. Open account **Preferences** and select **API**.
3. Choose **Create API Key** and copy the key.
4. In SDJ, open **Help → Set Up SteamGridDB API Key** and paste it.

SDJ keeps the key only on your device, in your library folder. Updates keep it. Never post or share the key.

## What "Open SDJ Folder" means

**Manage ▾ → Open SDJ Folder** opens your library folder: your drives and games (`data/`), your covers
(`assets/covers/<Jewel>/<Game>/`) and your settings. It's separate from the app itself, so updating or
reinstalling never touches it. Copy this folder to back up your library.
