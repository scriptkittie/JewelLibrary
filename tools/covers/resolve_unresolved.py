#!/usr/bin/env python3
import difflib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PySide6.QtGui import QImage, QImageReader

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from steamdeck_jewels.app import GAMES_FILE, cover_directories, cover_directory, cover_folder_name

BASE = PROJECT_ROOT
REPORTS = PROJECT_ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)
UNRESOLVED_FILE = REPORTS / "unresolved.txt"
COMPLETED_FILE = REPORTS / "completed.txt"
REVIEW_FILE = REPORTS / "cover-review.txt"
VALID_COVER_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
REQUIRED_SIZE = (600, 900)
SGDB_KEY_FILE = PROJECT_ROOT / ".secrets" / "steamgriddb.key"


def parse_records(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) % 3:
        raise ValueError("unresolved.txt must contain repeating Drive, Title, Reason lines")
    return [tuple(lines[index:index + 3]) for index in range(0, len(lines), 3)]


def write_records(records):
    text = "".join(f"{drive}\n{title}\n{reason}\n" for drive, title, reason in records)
    UNRESOLVED_FILE.write_text(text, encoding="utf-8")


def publish_review(games):
    """Freshly audit all games, then replace only the managed cover-report text files."""
    completed = []
    unresolved = []
    by_drive = {}
    for game in games:
        valid, status = cover_status(game)
        bucket = by_drive.setdefault(game["drive"], {"complete": 0, "unresolved": 0})
        if valid:
            completed.append((game["drive"], game["title"], status))
            bucket["complete"] += 1
        else:
            unresolved.append((game["drive"], game["title"], status))
            bucket["unresolved"] += 1

    # Delete only reports owned by this tool, and only after the fresh scan succeeded.
    for report in (UNRESOLVED_FILE, COMPLETED_FILE, REVIEW_FILE):
        if report.exists():
            report.unlink()

    lines = [
        "SteamDeck Jewels cover review",
        "",
        f"Games scanned: {len(games)}",
        f"Complete 600x900 covers: {len(completed)}",
        f"Unresolved covers: {len(unresolved)}",
        "",
    ]
    for drive in by_drive:
        counts = by_drive[drive]
        lines.append(
            f"{drive}: {counts['complete']} complete, {counts['unresolved']} unresolved"
        )
    lines.extend(("", "Status: READY" if not unresolved else "Status: REVIEW REQUIRED"))
    REVIEW_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if unresolved:
        write_records(unresolved)
        COMPLETED_FILE.write_text(
            "".join(f"{drive}\n{title}\n{status}\n" for drive, title, status in completed),
            encoding="utf-8",
        )
    return completed, unresolved


def normalized(value):
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def match_game(games, drive, title):
    choices = [game for game in games if game["drive"].casefold() == drive.casefold()]
    exact = next((game for game in choices if normalized(game["title"]) == normalized(title)), None)
    if exact:
        return exact
    matches = difflib.get_close_matches(title, [game["title"] for game in choices], n=1, cutoff=0.55)
    return next((game for game in choices if game["title"] == matches[0]), None) if matches else None


def cover_status(game):
    images = sorted(
        (
            path
            for folder in cover_directories(game) if folder.is_dir()
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in VALID_COVER_SUFFIXES
        ),
        key=lambda path: (path.parent.name.casefold(), path.name.casefold()),
    )
    if not images:
        return False, "Missing JPG/JPEG, PNG, or WebP cover"
    problems = []
    for path in images:
        reader = QImageReader(str(path))
        size = reader.size()
        if not size.isValid():
            problems.append(f"{path.name} is not a readable image")
        elif (size.width(), size.height()) == REQUIRED_SIZE:
            return True, f"{path.name} is 600x900"
        else:
            problems.append(f"{path.name} is {size.width()}x{size.height()}, not 600x900")
    return False, "; ".join(problems)


def audit_records(games, previous):
    previous_by_game = {}
    for record in previous:
        game = match_game(games, record[0], record[1])
        if game:
            previous_by_game[game["id"]] = record
    records = []
    for game in games:
        valid, reason = cover_status(game)
        if valid:
            continue
        old = previous_by_game.get(game["id"])
        if old and re.search(r"AppID\s+\d+", old[2], re.IGNORECASE):
            reason = f"{reason}; {old[2]}"
        records.append((game["drive"], game["title"], reason))
    return records


def image_urls(appid):
    bases = (
        "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps",
        "https://cdn.cloudflare.steamstatic.com/steam/apps",
    )
    names = ("library_600x900.jpg",)
    return [f"{base}/{appid}/{name}" for base in bases for name in names]


def save_download(url, destination, headers=None):
    request = urllib.request.Request(url, headers=headers or {"User-Agent": "SteamDeckJewels/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read()
        content_type = response.headers.get_content_type()
    image = QImage.fromData(data)
    if (
        not content_type.startswith("image/")
        or len(data) <= 1000
        or image.isNull()
        or (image.width(), image.height()) != REQUIRED_SIZE
    ):
        return False
    destination.mkdir(parents=True, exist_ok=True)
    suffix = ".png" if content_type == "image/png" else ".webp" if content_type == "image/webp" else ".jpg"
    for old_cover in destination.glob("cover.*"):
        old_cover.unlink()
    (destination / f"cover{suffix}").write_bytes(data)
    return True


def steamgriddb_key():
    environment_key = os.environ.get("STEAMGRIDDB_API_KEY", "").strip()
    if environment_key:
        return environment_key
    if SGDB_KEY_FILE.is_file():
        return SGDB_KEY_FILE.read_text(encoding="utf-8").strip()
    return ""


def steamgriddb_cover(appid, destination):
    key = steamgriddb_key()
    if not key:
        return None, "SteamGridDB is unavailable because no API key is configured."
    endpoint = (
        f"https://www.steamgriddb.com/api/v2/grids/steam/{appid}"
        "?dimensions=600x900&types=static&nsfw=any"
    )
    api_headers = {
        "Authorization": f"Bearer {key}",
        "User-Agent": "SteamDeckJewels/0.1",
    }
    try:
        request = urllib.request.Request(endpoint, headers=api_headers)
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        grids = payload.get("data") or []
        for grid in grids:
            url = grid.get("url")
            if url and save_download(url, destination):
                return url, None
        if grids:
            return None, "SteamGridDB returned grids, but none decoded as exactly 600x900."
        return None, f"SteamGridDB has no static 600x900 grid for AppID {appid}."
    except urllib.error.HTTPError as error:
        if error.code == 401:
            return None, "SteamGridDB rejected the configured API key."
        if error.code == 404:
            return None, f"SteamGridDB could not match AppID {appid}."
        return None, f"SteamGridDB returned HTTP error {error.code}."
    except (urllib.error.URLError, TimeoutError):
        return None, "SteamGridDB could not be reached; check the network connection."
    except (json.JSONDecodeError, KeyError, TypeError):
        return None, "SteamGridDB returned an unreadable response."


def download_cover(appid, destination):
    headers = {"User-Agent": "SteamDeckJewels/0.1"}
    for url in image_urls(appid):
        try:
            if save_download(url, destination, headers):
                return url, "Steam"
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            pass
    url, error = steamgriddb_cover(appid, destination)
    return (url, "SteamGridDB") if url else (None, error)


def is_steamgriddb_url(value):
    try:
        parsed = urllib.parse.urlparse(value)
        hostname = (parsed.hostname or "").casefold()
        return parsed.scheme == "https" and (
            hostname == "steamgriddb.com" or hostname.endswith(".steamgriddb.com")
        )
    except ValueError:
        return False


def download_direct_url(url, destination):
    if not is_steamgriddb_url(url):
        return False, "Only HTTPS links hosted by steamgriddb.com are accepted."
    try:
        if save_download(url, destination):
            return True, "SteamGridDB image downloaded and verified as 600x900."
        return False, "The link did not return a readable image that is exactly 600x900."
    except urllib.error.HTTPError as error:
        return False, f"SteamGridDB returned HTTP error {error.code} for that link."
    except (urllib.error.URLError, TimeoutError):
        return False, "The SteamGridDB image link could not be reached."


def prompt_for_appid(record, game):
    drive, title, reason = record
    destination = (
        cover_directory(game)
        if game else BASE / "assets" / "covers" / drive / cover_folder_name(title)
    )
    listed = re.search(r"AppID\s+(\d+)", reason, re.IGNORECASE)
    candidates = [listed.group(1)] if listed else []

    print(f"\n[{drive}] {title}")
    print(f"Reason: {reason}")
    print(f"Cover folder: {destination}")
    if game and game["title"] != title:
        print(f"Matched library title: {game['title']}")

    while True:
        if candidates:
            appid = candidates.pop(0)
            print(f"Trying AppID {appid}...")
        else:
            appid = input(
                "Enter a Steam AppID or SteamGridDB image URL, press Enter to recheck a manual cover, "
                "or q to continue: "
            ).strip()
            if appid.casefold() == "q":
                return False, "Skipped with q; AppID still unresolved"
            if not appid:
                if not game:
                    print("This title could not be matched to a library folder.")
                    continue
                valid, status = cover_status(game)
                print(f"Cover check: {status}")
                if valid:
                    print("Manual cover accepted.")
                    return True, ""
                print("Add or replace the image, then press Enter to check again.")
                continue
            if appid.startswith(("https://", "http://")):
                downloaded, message = download_direct_url(appid, destination)
                print(message)
                if downloaded:
                    return True, ""
                print("Try another URL or AppID, add the cover manually, or enter q to continue.")
                continue
            if not appid.isdigit():
                print("That is not a numeric AppID or SteamGridDB image URL. Try again, or enter q.")
                continue

        url, source = download_cover(appid, destination)
        if url:
            print(f"Saved cover using AppID {appid} from {source}")
            print(f"Source: {url}")
            return True, ""
        print(f"No cover was downloaded for AppID {appid}.")
        print(f"Details: {source}")
        print("Try looking up the game manually at https://www.steamgriddb.com/")
        print("Download a portrait cover and place it in the cover folder shown above.")
        print("Check the AppID and try another one, or enter q to continue.")


def main():
    if not UNRESOLVED_FILE.exists():
        print(f"Not found: {UNRESOLVED_FILE}")
        return 1
    if not GAMES_FILE.is_file():
        print("No library yet. Open SteamDeck Jewels and add a game first.")
        return 0
    games = json.loads(GAMES_FILE.read_text(encoding="utf-8"))
    previous = parse_records(UNRESOLVED_FILE.read_text(encoding="utf-8"))
    records = audit_records(games, previous)
    write_records(records)
    remaining = []

    print("SteamDeck Jewels cover audit and unresolved-cover helper")
    print(f"Checked {len(games)} games; {len(records)} need a valid 600x900 cover.")
    print("For each game, enter a Steam AppID or direct SteamGridDB image URL.")
    print("AppIDs try Steam first and then SteamGridDB automatically.")
    print("If an AppID does not work, you will be asked again.")
    print("You can also add a JPG/JPEG, PNG, or WebP manually and press Enter to recheck it.")
    print("Type q at any AppID prompt to leave that game unresolved and move forward.\n")

    try:
        for index, record in enumerate(records):
            game = match_game(games, record[0], record[1])
            resolved, reason = prompt_for_appid(record, game)
            if not resolved:
                remaining.append((record[0], record[1], reason))
            write_records(remaining + records[index + 1:])
    except (KeyboardInterrupt, EOFError):
        print("\nStopped. Progress already saved; run the helper again to resume.")
        return 130

    completed, unresolved = publish_review(games)
    print(f"\nFresh verification scan: {len(completed)} complete, {len(unresolved)} unresolved.")
    print(f"Review: {REVIEW_FILE}")
    if unresolved:
        print(f"Unresolved details: {UNRESOLVED_FILE}")
        print(f"Completed details: {COMPLETED_FILE}")
    else:
        print("All covers are resolved. Temporary unresolved/completed reports were removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
