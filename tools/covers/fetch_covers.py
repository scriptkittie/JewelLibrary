#!/usr/bin/env python3
"""Automatically search Steam for missing JewelLibrary covers, then publish a fresh review."""
import difflib
import importlib.util
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cover_resolver", BASE / "resolve_unresolved.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)

from steamdeck_jewels.app import GAMES_FILE, cover_directory

# Optional search-term overrides for titles Steam lists under a different name:
# {"Your library title": "Name as listed on Steam"}
ALIASES = {}


def normalized(value):
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def title_score(wanted, candidate):
    left, right = normalized(wanted), normalized(candidate)
    score = difflib.SequenceMatcher(None, left, right).ratio()
    if left in right or right in left:
        score += 0.12
    return min(score, 1.0)


def search_steam(title):
    query = urllib.parse.urlencode({"term": ALIASES.get(title, title), "l": "english", "cc": "US"})
    request = urllib.request.Request(
        f"https://store.steampowered.com/api/storesearch/?{query}",
        headers={"User-Agent": "SteamDeckJewels/0.1"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        items = json.loads(response.read().decode("utf-8")).get("items", [])
    ranked = sorted(
        ((title_score(ALIASES.get(title, title), item.get("name", "")), item) for item in items),
        reverse=True,
        key=lambda pair: pair[0],
    )
    return ranked[0] if ranked and ranked[0][0] >= 0.68 else (0.0, None)


def main():
    if not GAMES_FILE.is_file():
        print("No library yet. Open SteamDeck Jewels and add a game first.")
        return 0
    games = json.loads(GAMES_FILE.read_text(encoding="utf-8"))
    missing = [game for game in games if not resolver.cover_status(game)[0]]
    print(f"SteamDeck Jewels automatic cover fetcher: {len(missing)} cover(s) need attention.")
    for index, game in enumerate(missing, 1):
        print(f"[{index}/{len(missing)}] {game['drive']} / {game['title']}")
        try:
            score, item = search_steam(game["title"])
            if not item:
                print("  No confident Steam match; leaving for interactive review.")
                continue
            appid = str(item["id"])
            url, source = resolver.download_cover(appid, cover_directory(game))
            if url:
                print(f"  Saved {source} cover using AppID {appid} ({item.get('name', '')}).")
            else:
                print(f"  AppID {appid} failed: {source}")
        except Exception as error:
            print(f"  Fetch failed: {error}")
    completed, unresolved = resolver.publish_review(games)
    print(f"\nVerified: {len(completed)} complete, {len(unresolved)} unresolved.")
    print(f"Review: {resolver.REVIEW_FILE}")
    return 0 if not unresolved else 2


if __name__ == "__main__":
    sys.exit(main())
