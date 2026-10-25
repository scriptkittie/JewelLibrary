"""Update an installed SteamDeck Jewels from the latest GitHub release.

The app checks for a newer release and, when the user agrees, starts this module as a separate
process and quits. This process waits for the app to close, downloads the release ZIP for this
platform, runs its setup in update mode (which keeps data/, covers and the SteamGridDB key),
records the result for the app to show, and reopens the app. Standard library only.

    python -m steamdeck_jewels.updater --install <folder> [--check-only] [--pause]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

# The GitHub repository releases are published to, as "owner/name".
# SDJ_GITHUB_REPO in the environment overrides it.
GITHUB_REPO = "scriptkittie/JewelLibrary"

USER_AGENT = "SteamDeckJewels-Updater"
STATUS_FILE = ".update-status.json"


def _platform():
    if os.name == "nt":
        return "Windows"
    try:
        release = Path("/etc/os-release").read_text(encoding="utf-8")
    except OSError:
        release = ""
    return "SteamOS" if re.search(r"^ID=\"?steamos", release, re.M) else "Linux"


PLATFORM = _platform()
# The SteamOS and Linux downloads contain the same files, so either works on the other.
ASSET_PREFERENCE = {"Windows": ["Windows"], "SteamOS": ["SteamOS", "Linux"], "Linux": ["Linux", "SteamOS"]}


class UpdateError(Exception):
    """A problem worth showing the user as-is."""


def configured_repo():
    return os.environ.get("SDJ_GITHUB_REPO", GITHUB_REPO).strip()


def version_tuple(text):
    numbers = re.findall(r"\d+", text or "")
    return tuple(int(n) for n in numbers[:3]) if numbers else (0,)


def installed_version(install):
    init = Path(install) / "src" / "steamdeck_jewels" / "__init__.py"
    if init.is_file():
        match = re.search(r'__version__\s*=\s*"([^"]+)"', init.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    return "0"


def update_blocker(install):
    """Explain why this copy can't update itself, or return None if it can."""
    install = Path(install)
    if getattr(sys, "frozen", False):
        return "This standalone build can't update itself. Download the latest release from GitHub."
    if (install / ".git").exists():
        return "This is a development copy. Update it with git pull instead."
    setup = install / "platform" / ("windows/setup.bat" if os.name == "nt" else "steamos/setup.sh")
    if not setup.is_file():
        return "This copy wasn't installed with setup, so it can't update itself."
    if not configured_repo():
        return "Updates aren't set up yet: no GitHub repository is configured."
    return None


def _request(url, timeout):
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    )
    return urllib.request.urlopen(request, timeout=timeout)


def latest_release():
    """Return (tag, asset) for the newest release; asset is None if it lacks this platform's ZIP."""
    repo = configured_repo()
    try:
        with _request(f"https://api.github.com/repos/{repo}/releases/latest", 15) as response:
            release = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise UpdateError("No published release was found on GitHub yet.") from error
        raise UpdateError(f"GitHub returned an error: {error.code} {error.reason}") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise UpdateError("Couldn't reach GitHub. Check your internet connection.") from error
    assets = [item for item in release.get("assets", []) if item.get("name", "").endswith(".zip")]
    asset = next(
        (
            item for name in ASSET_PREFERENCE[PLATFORM] for item in assets
            if item["name"].startswith(f"SteamDeckJewels-{name}-")
        ),
        None,
    )
    return release.get("tag_name", ""), asset


def check(install):
    """Return (current, latest_tag, newer) for the installed copy. Raises UpdateError."""
    blocker = update_blocker(install)
    if blocker:
        raise UpdateError(blocker)
    current = installed_version(install)
    tag, _ = latest_release()
    return current, tag, version_tuple(tag) > version_tuple(current)


def _download(url, destination):
    with _request(url, 120) as response, open(destination, "wb") as out:
        while chunk := response.read(1 << 16):
            out.write(chunk)


def _wait_for_exit(pid, timeout=60):
    if not pid:
        return
    deadline = time.time() + timeout
    if os.name == "nt":
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x00100000, False, int(pid))  # SYNCHRONIZE
        if handle:
            ctypes.windll.kernel32.WaitForSingleObject(handle, int(timeout * 1000))
            ctypes.windll.kernel32.CloseHandle(handle)
        return
    while time.time() < deadline:
        try:
            os.kill(int(pid), 0)
        except OSError:
            return
        time.sleep(0.3)


def _run_setup(extracted, install):
    env = dict(os.environ, SDJ_INSTALL=str(install), SDJ_NONINTERACTIVE="1")
    if os.name == "nt":
        setup = next(extracted.rglob("platform/windows/setup.bat"), None)
        command = ["cmd", "/c", str(setup), "update"] if setup else None
        flags = subprocess.CREATE_NO_WINDOW
    else:
        setup = next(extracted.rglob("platform/steamos/setup.sh"), None)
        command = ["bash", str(setup), "update"] if setup else None
        flags = 0
    if not command:
        raise UpdateError("The downloaded release doesn't contain a SteamDeck Jewels setup script.")
    log = Path(install) / "update.log"
    with open(log, "w", encoding="utf-8") as out:
        status = subprocess.call(command, env=env, stdout=out, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, creationflags=flags)
    if status != 0:
        raise UpdateError(f"Setup reported an error (code {status}). Details are in {log}.")


def relaunch(install):
    install = Path(install)
    if os.name == "nt":
        subprocess.Popen(
            ["cmd", "/c", str(install / "platform" / "windows" / "run.bat")],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
            close_fds=True,
        )
    else:
        subprocess.Popen([str(install / "platform" / "steamos" / "run.sh")],
                         start_new_session=True, close_fds=True)


def write_status(install, ok, message):
    path = Path(install) / STATUS_FILE
    path.write_text(json.dumps({"ok": ok, "message": message}), encoding="utf-8")


def take_status(install):
    """Return and clear the result of the last update, if there is one."""
    path = Path(install) / STATUS_FILE
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    finally:
        path.unlink(missing_ok=True)


def apply_update(install, wait_pid=None, force=False, say=print):
    """Download and install the latest release. Returns a message; raises UpdateError."""
    install = Path(install).resolve()
    _wait_for_exit(wait_pid)
    blocker = update_blocker(install)
    if blocker:
        raise UpdateError(blocker)
    current = installed_version(install)
    tag, asset = latest_release()
    if version_tuple(tag) <= version_tuple(current) and not force:
        return f"You already have the latest version ({current})."
    if not asset:
        raise UpdateError(f"Release {tag} has no {PLATFORM} download attached.")
    with tempfile.TemporaryDirectory(prefix="SteamDeckJewelsUpdate-") as temp:
        temp_dir = Path(temp)
        archive = temp_dir / asset["name"]
        say(f"Downloading {asset['name']}...")
        _download(asset["browser_download_url"], archive)
        extracted = temp_dir / "extracted"
        with zipfile.ZipFile(archive) as zip_file:
            zip_file.extractall(extracted)
        say("Installing the update (your games, drives, covers and API key are kept)...")
        _run_setup(extracted, install)
    return f"Updated from {current} to {tag.lstrip('v')}."


def start_background_update(install):
    """Launch this module as its own process to update after the app closes, then reopen it."""
    install = Path(install).resolve()
    python = Path(sys.executable)
    env = dict(os.environ, PYTHONPATH=str(install / "src"))
    command = [str(python), "-m", "steamdeck_jewels.updater", "--install", str(install),
               "--wait-pid", str(os.getpid()), "--relaunch"]
    if os.name == "nt":
        subprocess.Popen(command, env=env, close_fds=True,
                         creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
    else:
        subprocess.Popen(command, env=env, close_fds=True, start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Update SteamDeck Jewels from GitHub.")
    parser.add_argument("--install", required=True, help="the installed SteamDeck Jewels folder")
    parser.add_argument("--check-only", action="store_true", help="only report whether an update exists")
    parser.add_argument("--wait-pid", type=int, help="wait for this process to exit first")
    parser.add_argument("--relaunch", action="store_true", help="reopen the app afterwards")
    parser.add_argument("--force", action="store_true", help="reinstall even if already up to date")
    parser.add_argument("--pause", action="store_true", help="wait for Enter before closing")
    args = parser.parse_args(argv)
    install = Path(args.install).resolve()
    status = 0
    try:
        if args.check_only:
            current, tag, newer = check(install)
            print(f"Installed {current}; latest release {tag}; "
                  + ("an update is available." if newer else "up to date."))
        else:
            message = apply_update(install, args.wait_pid, args.force)
            print(message)
            if args.relaunch:
                write_status(install, True, message)
    except Exception as error:  # report every failure instead of dying silently
        status = 1
        message = str(error) if isinstance(error, UpdateError) else f"Update failed: {error}"
        print(message)
        if args.relaunch:
            write_status(install, False, message)
    if args.relaunch:
        relaunch(install)
    if args.pause:
        input("\nPress Enter to close...")
    return status


if __name__ == "__main__":
    sys.exit(main())
