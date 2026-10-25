#!/usr/bin/env python3
"""Build the Windows, SteamOS and Linux release ZIPs from a clean checkout.

    python tools/package_release.py

Writes release/SteamDeckJewels-Windows-<version>.zip, -SteamOS-<version>.zip and
-Linux-<version>.zip. Only files tracked for release are
included, so personal libraries, covers, API keys and virtual environments never ship.
"""
import re
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "release"

COMMON = [
    "README.md",
    "LICENSE",
    "START_HERE.txt",
    "requirements.txt",
    "pyproject.toml",
    "src/steamdeck_jewels",
    "assets/jewels",
    "assets/covers/_placeholder.svg",
    "data/README.md",
    "reports/README.md",
    "docs",
    "tools",
]
PLATFORM = {
    "Windows": [
        "platform/windows",
        "setup-windows.bat",
        "run-windows.bat",
        "build-windows.bat",
        "fetch-covers.bat",
        "resolve-covers.bat",
        "SteamDeckJewels.spec",
    ],
    "SteamOS": [
        "platform/steamos",
        "setup-steamos.sh",
        "run-steamos.sh",
        "build-steamos.sh",
    ],
    # Same scripts as SteamOS, plus Linux-named entry points.
    "Linux": [
        "platform/steamos",
        "setup-linux.sh",
        "run-linux.sh",
        "build-linux.sh",
        "setup-steamos.sh",
        "run-steamos.sh",
        "build-steamos.sh",
    ],
}
SKIP_PARTS = {"__pycache__", ".venv", ".build-venv", ".secrets"}


def version():
    text = (ROOT / "src" / "steamdeck_jewels" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'__version__\s*=\s*"([^"]+)"', text).group(1)


def files_for(entries):
    for entry in entries:
        path = ROOT / entry
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and not SKIP_PARTS.intersection(child.relative_to(ROOT).parts):
                    yield child
        elif entry != "LICENSE":
            raise FileNotFoundError(f"Release file missing: {entry}")


def build(platform_name, release_version):
    top = f"SteamDeckJewels-{platform_name}"
    target = OUT / f"{top}-{release_version}.zip"
    OUT.mkdir(exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files_for(COMMON + PLATFORM[platform_name]):
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(f"{top}/{relative}")  # forward slashes for every OS
            data = path.read_bytes()
            mode = 0o644
            if path.suffix in {".bat", ".ps1"}:
                data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            elif path.suffix in {".sh", ".py"}:
                data = data.replace(b"\r\n", b"\n")
                if path.suffix == ".sh":
                    mode = 0o755
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return target


def main():
    release_version = version()
    for platform_name in PLATFORM:
        print(f"Built {build(platform_name, release_version).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
