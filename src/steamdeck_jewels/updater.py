"""Keep SteamDeck Jewels up to date from GitHub Releases.

Installed builds update themselves:

* Windows installer: download the new SteamDeckJewels-Setup.exe and run it silently. It closes the
  app, installs over it and reopens it.
* Linux / Steam Deck AppImage: download the new AppImage, swap it in place of the running one and
  reopen it.

The library lives in a separate per-user folder, so updates never touch it. After the restart the
app reports how the update went (see take_result).

Older script-based installs (setup-windows.bat / setup-steamos.sh) are told to switch to the
installer. Standard library only.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

# The GitHub repository releases are published to, as "owner/name".
# SDJ_GITHUB_REPO in the environment overrides it.
GITHUB_REPO = "scriptkittie/JewelLibrary"

WINDOWS_ASSET = "SteamDeckJewels-Setup.exe"
LINUX_ASSET = "SteamDeckJewels-x86_64.AppImage"
RESULT_FILE = ".update-pending.json"
USER_AGENT = "SteamDeckJewels-Updater"


class UpdateError(Exception):
    """A problem worth showing the user as-is."""


def configured_repo():
    return os.environ.get("SDJ_GITHUB_REPO", GITHUB_REPO).strip()


def current_version():
    try:
        from steamdeck_jewels import __version__
    except ImportError:  # pragma: no cover - run as a loose script
        from __init__ import __version__  # type: ignore
    return __version__


def version_tuple(text):
    numbers = re.findall(r"\d+", text or "")
    return tuple(int(n) for n in numbers[:3]) if numbers else (0,)


def install_kind():
    """'windows' (installer), 'appimage', or None when this copy can't update itself."""
    if getattr(sys, "frozen", False):
        if os.name == "nt":
            return "windows"
        if os.environ.get("APPIMAGE"):
            return "appimage"
    return None


def update_blocker():
    """Explain why this copy can't update itself, or return None if it can."""
    if not configured_repo():
        return "Updates aren't set up: no GitHub repository is configured."
    if install_kind():
        return None
    if getattr(sys, "frozen", False):
        return "This copy can't update itself. Download the latest version from the Releases page."
    return ("This copy was set up from the source files, so it can't update itself.\n\n"
            f"Download the installer from https://github.com/{configured_repo()}/releases/latest "
            "and install it once; after that, updates happen inside the app.")


def _request(url, timeout):
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    )
    return urllib.request.urlopen(request, timeout=timeout)


def latest_release():
    """Return (tag, asset or None) for the newest release and this install type."""
    try:
        with _request(f"https://api.github.com/repos/{configured_repo()}/releases/latest", 15) as response:
            release = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise UpdateError("No published release was found on GitHub yet.") from error
        raise UpdateError(f"GitHub returned an error: {error.code} {error.reason}") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise UpdateError("Couldn't reach GitHub. Check your internet connection.") from error
    wanted = {"windows": WINDOWS_ASSET, "appimage": LINUX_ASSET}.get(install_kind())
    asset = next((a for a in release.get("assets", []) if a.get("name") == wanted), None)
    return release.get("tag_name", ""), asset


def check():
    """Return (current, latest_tag, newer). Raises UpdateError."""
    blocker = update_blocker()
    if blocker:
        raise UpdateError(blocker)
    current = current_version()
    tag, _ = latest_release()
    return current, tag, version_tuple(tag) > version_tuple(current)


def download(asset, destination, progress=None):
    """Download a release asset to destination, reporting (done, total) bytes."""
    total = int(asset.get("size") or 0)
    done = 0
    try:
        with _request(asset["browser_download_url"], 60) as response, open(destination, "wb") as out:
            while chunk := response.read(1 << 16):
                out.write(chunk)
                done += len(chunk)
                if progress:
                    progress(done, total)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise UpdateError(f"The download didn't finish: {error}") from error
    if total and done != total:
        raise UpdateError("The download was incomplete. Please try again.")


def _remember(user_home, target):
    Path(user_home).mkdir(parents=True, exist_ok=True)
    (Path(user_home) / RESULT_FILE).write_text(
        json.dumps({"from": current_version(), "to": target.lstrip("v"), "at": time.time()}),
        encoding="utf-8",
    )


def install(user_home, progress=None):
    """Download the latest release and hand over to it. The caller must quit right after."""
    blocker = update_blocker()
    if blocker:
        raise UpdateError(blocker)
    tag, asset = latest_release()
    if not asset:
        raise UpdateError(f"Release {tag} doesn't include a download for this system yet.")
    kind = install_kind()
    if kind == "windows":
        target = Path(tempfile.gettempdir()) / WINDOWS_ASSET
        download(asset, target, progress)
        _remember(user_home, tag)
        # The installer closes this app, installs over it and reopens it (/RELAUNCH=1).
        subprocess.Popen(
            [str(target), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/RELAUNCH=1"],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )
        return
    appimage = Path(os.environ["APPIMAGE"])
    partial = appimage.with_name(appimage.name + ".download")
    try:
        download(asset, partial, progress)
        partial.chmod(0o755)
        os.replace(partial, appimage)  # safe on Linux: the running copy keeps its old file
    except OSError as error:
        raise UpdateError(f"Couldn't replace {appimage.name}: {error}") from error
    finally:
        partial.unlink(missing_ok=True)
    _remember(user_home, tag)
    subprocess.Popen([str(appimage)], start_new_session=True, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def take_result(user_home):
    """After a restart, return (ok, message) for the update that just ran, or None."""
    path = Path(user_home) / RESULT_FILE
    if not path.is_file():
        return None
    try:
        pending = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pending = {}
    path.unlink(missing_ok=True)
    target = pending.get("to", "")
    if target and version_tuple(current_version()) >= version_tuple(target):
        return True, f"Updated from {pending.get('from', '?')} to {current_version()}."
    if time.time() - pending.get("at", 0) > 600:
        return None  # stale marker from an update that was abandoned long ago
    return False, (f"The update to {target} didn't finish, so you're still on {current_version()}. "
                   "You can try again from Help → Check for Updates.")
