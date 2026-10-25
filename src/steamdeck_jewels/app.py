#!/usr/bin/env python3
import argparse, json, os, re, sys, subprocess, shutil, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
from PySide6.QtCore import Qt, QSize, QTimer, QEvent, QObject, Signal
from PySide6.QtGui import QPixmap, QKeySequence, QAction, QImageReader, QIcon, QFont, QFontMetrics, QPainter, QLinearGradient, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QMessageBox, QComboBox,
    QInputDialog, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QCheckBox,
    QMenu, QScroller, QListWidget, QListWidgetItem, QSizePolicy, QProgressDialog
)

try:
    from steamdeck_jewels import updater
except ImportError:  # run as a plain script (PyInstaller entry point)
    import updater

FROZEN = getattr(sys, "frozen", False)  # running from the Windows installer or the AppImage


def user_data_dir():
    """Where an installed build keeps the library (drives, games, covers, API key)."""
    override = os.environ.get("SDJ_HOME", "").strip()
    if override:
        return Path(override)
    if os.name == "nt":
        # The same folder older script-based installs used, so existing libraries carry over.
        local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(local) / "SteamDeckJewels"
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "SteamDeckJewels"


if FROZEN:
    # Program files (gem icons, placeholder) are bundled read-only inside the app;
    # the library lives in the per-user data folder and survives updates and reinstalls.
    RESOURCES = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    USER_HOME = user_data_dir()
else:
    # Running from source or an older script-based install: everything in one folder.
    RESOURCES = USER_HOME = Path(__file__).resolve().parents[2]
DATA = USER_HOME / "data"
COVERS = USER_HOME / "assets" / "covers"
JEWELS = RESOURCES / "assets" / "jewels"
PLACEHOLDER_COVER = RESOURCES / "assets" / "covers" / "_placeholder.svg"
SECRETS = USER_HOME / ".secrets"
GAMES_FILE = DATA / "games.json"
DRIVES_FILE = DATA / "drives.json"

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)

def migrate_legacy_library():
    """Copy a library from an older Linux/SteamOS script install into the new data folder."""
    if not FROZEN or os.name == "nt" or GAMES_FILE.exists():
        return
    legacy = Path.home() / "Applications" / "SteamDeckJewels"
    if not (legacy / "data" / "games.json").is_file():
        return
    DATA.mkdir(parents=True, exist_ok=True)
    for name in ("games.json", "drives.json"):
        if (legacy / "data" / name).is_file():
            shutil.copy2(legacy / "data" / name, DATA / name)
    for folder, target in ((legacy / "assets" / "covers", COVERS), (legacy / ".secrets", SECRETS)):
        if folder.is_dir():
            shutil.copytree(folder, target, dirs_exist_ok=True)

def ensure_data_files():
    """Create empty library files on first run so a fresh install or build always starts."""
    migrate_legacy_library()
    DATA.mkdir(parents=True, exist_ok=True)
    COVERS.mkdir(parents=True, exist_ok=True)
    for path, empty in ((DRIVES_FILE, {}), (GAMES_FILE, [])):
        if not path.is_file():
            save_json(path, empty)

def cover_folder_name(title):
    """Convert a game title to a Windows-safe folder name."""
    name = re.sub(r'[<>:"/\\|?*]', " -", title)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or "Untitled"

def cover_directory(game):
    """Return the canonical Jewel/[NSFW]/Game cover directory."""
    root = COVERS / game["drive"]
    if game.get("nsfw"):
        root = root / "NSFW"
    return root / cover_folder_name(game["title"])

def cover_directories(game):
    """Return the canonical folder plus equivalent title folders inside the same gem."""
    canonical = cover_directory(game)
    folders = [canonical]
    search_roots = [canonical.parent]
    if game.get("nsfw"):
        search_roots.append(COVERS / game["drive"])
    match_key = re.sub(r"[^a-z0-9]+", "", game["title"].casefold())
    for gem_folder in search_roots:
        if not gem_folder.is_dir():
            continue
        for candidate in gem_folder.iterdir():
            candidate_key = re.sub(r"[^a-z0-9]+", "", candidate.name.casefold())
            if candidate.is_dir() and candidate != canonical and candidate_key == match_key:
                folders.append(candidate)
    return folders

def find_cover(game):
    """Prefer an explicit cover, then the first image in the title's cover folder."""
    if game.get("cover"):
        return USER_HOME / game["cover"]
    supported = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".svg"}
    for folder in cover_directories(game):
        if folder.is_dir():
            images = sorted(
                (path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in supported),
                key=lambda path: path.name.casefold(),
            )
            if images:
                return images[0]
    return PLACEHOLDER_COVER

def _download_bytes(url, headers=None):
    request = urllib.request.Request(
        url, headers=headers or {"User-Agent": "SteamDeckJewels/0.2"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()

def _validated_cover(data):
    from PySide6.QtGui import QImage
    image = QImage.fromData(data)
    return not image.isNull() and (image.width(), image.height()) == (600, 900)

def _steamgriddb_cover(appid):
    key_file = SECRETS / "steamgriddb.key"
    key = os.environ.get("STEAMGRIDDB_API_KEY", "").strip()
    if not key and key_file.is_file():
        key = key_file.read_text(encoding="utf-8").strip()
    if not key:
        raise ValueError("SteamGridDB fallback needs a configured API key.")
    endpoint = (
        f"https://www.steamgriddb.com/api/v2/grids/steam/{appid}"
        "?dimensions=600x900&types=static&nsfw=any"
    )
    payload = json.loads(_download_bytes(endpoint, {
        "Authorization": f"Bearer {key}", "User-Agent": "SteamDeckJewels/0.2"
    }).decode("utf-8"))
    for grid in payload.get("data") or []:
        url = grid.get("url")
        if url:
            data = _download_bytes(url)
            if _validated_cover(data):
                return data, Path(urllib.parse.urlparse(url).path).suffix.lower() or ".png", "SteamGridDB"
    raise ValueError(f"SteamGridDB has no valid 600x900 cover for AppID {appid}.")

def fetch_cover_by_appid(appid):
    if not str(appid).isdigit():
        raise ValueError("Steam AppID must contain numbers only.")
    # Only the 1x library image is exactly 600x900; the 2x variant never validates.
    names = ("library_600x900.jpg",)
    bases = (
        "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps",
        "https://cdn.cloudflare.steamstatic.com/steam/apps",
    )
    for base in bases:
        for name in names:
            try:
                data = _download_bytes(f"{base}/{appid}/{name}")
                if _validated_cover(data):
                    return data, ".jpg", "Steam"
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
                pass
    return _steamgriddb_cover(str(appid))

def _normalized_title(text):
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()

def search_steam_results(title):
    """Return Steam store search results in Steam's own relevance order."""
    if not title.strip():
        raise ValueError("Enter a game name to search Steam.")
    query = urllib.parse.urlencode({"term": title, "l": "english", "cc": "US"})
    payload = json.loads(_download_bytes(
        f"https://store.steampowered.com/api/storesearch/?{query}"
    ).decode("utf-8"))
    items = [item for item in payload.get("items") or [] if item.get("id")]
    if not items:
        raise ValueError(f"Steam could not find a match for {title}.")
    return items

def preferred_steam_result(title, items):
    """Pre-select an exact title match if there is one, otherwise Steam's top result."""
    wanted = _normalized_title(title)
    for index, item in enumerate(items):
        if _normalized_title(item.get("name", "")) == wanted:
            return index
    return 0

def _fetch_thumbnails(items):
    def fetch(url):
        try:
            return _download_bytes(url) if url else None
        except Exception:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(fetch, [item.get("tiny_image", "") for item in items]))

def fetch_cover_from_url(url):
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").casefold()
    if parsed.scheme != "https" or not (
        hostname == "steamgriddb.com" or hostname.endswith(".steamgriddb.com")
    ):
        raise ValueError("Use a direct HTTPS image URL hosted by steamgriddb.com.")
    data = _download_bytes(url)
    if not _validated_cover(data):
        raise ValueError("That URL did not return a readable image exactly 600x900.")
    return data, Path(parsed.path).suffix.lower() or ".png", "SteamGridDB URL"

COVER_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".svg"}

def prepare_cover(cover_source="", cover_data=None, cover_suffix=""):
    """Validate a local file or downloaded bytes and return (bytes, suffix)."""
    if cover_data is None:
        source = Path(cover_source) if cover_source else None
        if not source or not source.is_file() or source.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ValueError("Choose a JPG/JPEG, PNG, or WebP cover image.")
        size = QImageReader(str(source)).size()
        if not size.isValid() or (size.width(), size.height()) != (600, 900):
            dimensions = f"{size.width()}x{size.height()}" if size.isValid() else "unreadable"
            raise ValueError(f"The selected cover is {dimensions}; it must be exactly 600x900.")
        return source.read_bytes(), source.suffix.lower()
    if not _validated_cover(cover_data):
        raise ValueError("The downloaded cover is not a readable 600x900 image.")
    return cover_data, cover_suffix

def replace_game_cover(game, cover_data, cover_suffix):
    """Install a new cover, moving any previous images into a _replaced subfolder."""
    folder = cover_directory(game)
    folder.mkdir(parents=True, exist_ok=True)
    old_images = [
        path for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in COVER_IMAGE_SUFFIXES
    ]
    if old_images:
        backup = folder / "_replaced"
        backup.mkdir(exist_ok=True)
        for path in old_images:
            path.replace(backup / path.name)
    (folder / f"cover{cover_suffix}").write_bytes(cover_data)
    return folder

def add_game_to_library(
    games, drives, title, drive, cover_source="", cover_data=None, cover_suffix="", nsfw=False
):
    """Validate and persist a new game and its 600x900 cover."""
    title = title.strip()
    if not title:
        raise ValueError("Enter a game name.")
    if drive not in drives:
        raise ValueError("Choose a configured Jewel Drive.")
    if any(
        game["drive"].casefold() == drive.casefold()
        and game["title"].casefold() == title.casefold()
        for game in games
    ):
        raise ValueError(f"{title} already exists on {drive}.")

    cover_data, cover_suffix = prepare_cover(cover_source, cover_data, cover_suffix)

    game = {
        "id": max((item.get("id", 0) for item in games), default=0) + 1,
        "title": title,
        "drive": drive,
        "cover": "",
        "cover_url": "",
        "launch": {"type": "path", "target": "", "working_directory": "", "arguments": []},
        "favorite": False,
        "nsfw": bool(nsfw),
        "platform": "PC",
        "notes": "",
    }
    destination_folder = cover_directory(game)
    destination_folder.mkdir(parents=True, exist_ok=True)
    (destination_folder / f"cover{cover_suffix}").write_bytes(cover_data)
    games.append(game)
    try:
        save_json(GAMES_FILE, games)
    except Exception:
        games.pop()
        raise
    return game


def remove_game_from_library(games, game, delete_cover=False):
    """Remove one game record and optionally its unshared cover directory."""
    if game not in games:
        raise ValueError("That game is no longer in the library.")
    folder = cover_directory(game)
    shared_cover = any(
        other is not game and cover_directory(other) == folder for other in games
    )
    if delete_cover and shared_cover:
        raise ValueError("Another library entry uses the same cover folder.")

    index = games.index(game)
    removed = games.pop(index)
    try:
        save_json(GAMES_FILE, games)
    except Exception:
        games.insert(index, removed)
        raise

    if delete_cover and folder.is_dir():
        try:
            shutil.rmtree(folder)
        except Exception as error:
            raise OSError(
                f"The library entry was removed, but its cover folder could not be deleted: {error}"
            ) from error
    return folder


COVER_KEEP = "Keep current cover"
COVER_SEARCH = "Search Steam by game name"
COVER_APPID = "Steam AppID"
COVER_URL = "SteamGridDB image URL"
COVER_LOCAL = "Local image file"

class CoverSourceControls:
    """Cover-source picker shared by the Add Game and Edit Game dialogs."""

    def __init__(self, dialog, form, allow_keep=False):
        self.dialog = dialog
        self.source_type = QComboBox()
        modes = [COVER_SEARCH, COVER_APPID, COVER_URL, COVER_LOCAL]
        self.source_type.addItems([COVER_KEEP, *modes] if allow_keep else modes)
        self.source_type.currentTextChanged.connect(self.update_mode)
        form.addRow("Cover source:", self.source_type)
        cover_row = QHBoxLayout()
        self.cover = QLineEdit()
        self.browse = QPushButton("Browse…")
        self.browse.clicked.connect(self.choose_cover)
        cover_row.addWidget(self.cover, 1)
        cover_row.addWidget(self.browse)
        form.addRow("AppID / URL / File:", cover_row)
        self.update_mode()

    def mode(self):
        return self.source_type.currentText()

    def update_mode(self):
        mode = self.mode()
        local = mode == COVER_LOCAL
        self.cover.setReadOnly(local)
        self.cover.setEnabled(mode not in (COVER_SEARCH, COVER_KEEP))
        self.browse.setVisible(local)
        placeholders = {
            COVER_KEEP: "The existing cover stays as it is",
            COVER_SEARCH: "Uses the game name above; you pick from Steam's results",
            COVER_APPID: "Example: 105600",
            COVER_URL: "https://cdn2.steamgriddb.com/grid/....png",
            COVER_LOCAL: "Choose a 600x900 JPG, PNG, or WebP",
        }
        self.cover.clear()
        self.cover.setPlaceholderText(placeholders[mode])

    def choose_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self.dialog, "Choose 600x900 cover", "",
            "Cover images (*.jpg *.jpeg *.png *.webp)"
        )
        if path:
            self.cover.setText(path)

class AddGameDialog(QDialog):
    def __init__(self, drives, selected_drive="All", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Game")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title = QLineEdit()
        self.title.setPlaceholderText("Game name")
        form.addRow("Name:", self.title)
        self.drive = QComboBox()
        self.drive.addItems(drives)
        if selected_drive in drives:
            self.drive.setCurrentText(selected_drive)
        form.addRow("Jewel Drive:", self.drive)
        self.nsfw = QCheckBox("NSFW — store under this Jewel's NSFW cover folder")
        form.addRow("Content:", self.nsfw)
        self.cover_controls = CoverSourceControls(self, form)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class EditGameDialog(QDialog):
    def __init__(self, game, drives, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Edit {game["title"]}')
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title = QLineEdit(game["title"])
        form.addRow("Name:", self.title)
        self.drive = QComboBox()
        self.drive.addItems(drives)
        self.drive.setCurrentText(game["drive"])
        form.addRow("Jewel Drive:", self.drive)
        self.nsfw = QCheckBox("NSFW - store under this Jewel's NSFW cover folder")
        self.nsfw.setChecked(bool(game.get("nsfw")))
        form.addRow("Content:", self.nsfw)
        launch_row = QHBoxLayout()
        self.executable = QLineEdit(game.get("launch", {}).get("target", ""))
        self.executable.setPlaceholderText("Choose the game's .exe")
        browse = QPushButton("Browse...")
        browse.clicked.connect(self.choose_executable)
        launch_row.addWidget(self.executable, 1)
        launch_row.addWidget(browse)
        form.addRow("Game executable:", launch_row)
        self.cover_controls = CoverSourceControls(self, form, allow_keep=True)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def choose_executable(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose game executable", "", "Windows executables (*.exe);;All files (*)"
        )
        if path:
            self.executable.setText(path)

class SteamResultDialog(QDialog):
    """Let the user pick which Steam search result the cover should come from."""

    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.items = items
        self.setWindowTitle("Choose the Steam match")
        self.setMinimumSize(560, 460)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Steam results for “{title}”. Pick the one you mean:"))
        self.results = QListWidget()
        self.results.setIconSize(QSize(120, 45))
        thumbnails = _fetch_thumbnails(items)
        for item, thumbnail in zip(items, thumbnails):
            entry = QListWidgetItem(f'{item.get("name", "Unknown")}    (AppID {item["id"]})')
            if thumbnail:
                pixmap = QPixmap()
                if pixmap.loadFromData(thumbnail):
                    entry.setIcon(QIcon(pixmap))
            self.results.addItem(entry)
        self.results.setCurrentRow(preferred_steam_result(title, items))
        self.results.itemDoubleClicked.connect(lambda _: self.accept())
        layout.addWidget(self.results, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def chosen(self):
        return self.items[max(0, self.results.currentRow())]

class CoverChoiceCancelled(Exception):
    pass

def windows_volumes():
    """Return mounted Windows volume labels mapped to their drive roots."""
    if os.name != "nt":
        return {}
    import ctypes
    volumes = {}
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    for index in range(26):
        if not mask & (1 << index):
            continue
        root = f"{chr(65 + index)}:\\"
        label = ctypes.create_unicode_buffer(261)
        if ctypes.windll.kernel32.GetVolumeInformationW(
            root, label, len(label), None, None, None, None, 0
        ):
            volumes[label.value.casefold()] = root
    return volumes

def find_drive(drive_info, volumes=None):
    """Return the mounted path/drive letter for a configured jewel, if present."""
    for candidate in drive_info.get("mount_candidates", []):
        path = Path(os.path.expandvars(os.path.expanduser(candidate)))
        if path.exists():
            return str(path)
    labels = drive_info.get("volume_labels", [drive_info.get("label", "")])
    if os.name == "nt":
        volumes = windows_volumes() if volumes is None else volumes
        for label in labels:
            if label.casefold() in volumes:
                return volumes[label.casefold()]
        return None
    # Linux desktops mount removable cards per user: /run/media/<user>/<label> on SteamOS,
    # Fedora and Arch; /media/<user>/<label> on Ubuntu and Debian.
    import getpass
    user = getpass.getuser()
    for label in labels:
        for root in (Path("/run/media") / user, Path("/media") / user, Path("/media")):
            if label and (root / label).is_dir():
                return str(root / label)
    return None

class GameCard(QFrame):
    WIDTH = 205
    def __init__(self, game, drive_info, drive_location, launch_cb, edit_cb, remove_cb):
        super().__init__()
        self.game = game
        self.launch_cb = launch_cb
        self.edit_cb = edit_cb
        self.remove_cb = remove_cb
        self.setObjectName("card")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedWidth(self.WIDTH)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8,8,8,10)
        lay.setSpacing(7)

        cover = QLabel()
        cover.setFixedSize(187, 280)
        cover.setAlignment(Qt.AlignCenter)
        cover_path = find_cover(game)
        pix = QPixmap(str(cover_path))
        if not pix.isNull():
            cover.setPixmap(pix.scaled(187,280,Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation))
        lay.addWidget(cover)

        title = QLabel(game["title"])
        title.setWordWrap(True)
        title.setObjectName("title")
        title.setFixedHeight(42)
        lay.addWidget(title)

        row = QHBoxLayout()
        jewel = QLabel()
        jewel.setFixedSize(22,22)
        jp = QPixmap(str(RESOURCES / drive_info["jewel"]))
        jewel.setPixmap(jp.scaled(22,22,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        row.addWidget(jewel)

        location = f"Connected at {drive_location}" if drive_location else "Offline"
        status = QLabel(f'{game["drive"]}  •  {location}')
        status.setObjectName("driveStatus")
        row.addWidget(status, 1)
        lay.addLayout(row)

        # Always reserve the NSFW tag's line so every card is the same height.
        adult = QLabel("NSFW" if game.get("nsfw") else "")
        adult.setObjectName("nsfw")
        adult.setFixedHeight(16)
        lay.addWidget(adult)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.launch_cb(self.game)
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.launch_cb(self.game)
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        edit_action = menu.addAction("Edit Game…")
        remove_action = menu.addAction("Remove from Library…")
        chosen = menu.exec(event.globalPos())
        if chosen == edit_action:
            self.edit_cb(self.game)
        elif chosen == remove_action:
            self.remove_cb(self.game)

class EdgeFade(QWidget):
    """A see-through gradient laid over one edge of the drive strip."""

    def __init__(self, parent, edge):
        super().__init__(parent)
        self.edge = edge
        self.setFixedWidth(40)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()

    def paintEvent(self, _event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        solid, clear = QColor("#0e0e16"), QColor(14, 14, 22, 0)
        if self.edge == Qt.LeftEdge:
            gradient.setColorAt(0, solid)
            gradient.setColorAt(1, clear)
        else:
            gradient.setColorAt(0, clear)
            gradient.setColorAt(1, solid)
        painter.fillRect(self.rect(), gradient)

class DriveStrip(QScrollArea):
    """Horizontally scrolling row of jewel filter buttons (touch, wheel and focus)."""

    def __init__(self):
        super().__init__()
        self.setObjectName("driveStrip")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        holder = QWidget()
        self.row = QHBoxLayout(holder)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setAlignment(Qt.AlignTop)
        self.row.addStretch()
        self.setWidget(holder)
        QScroller.grabGesture(self.viewport(), QScroller.TouchGesture)
        # Soft fades at either edge show there are more jewels to scroll to.
        self.left_fade = EdgeFade(self, Qt.LeftEdge)
        self.right_fade = EdgeFade(self, Qt.RightEdge)
        bar = self.horizontalScrollBar()
        bar.valueChanged.connect(self.update_fades)
        bar.rangeChanged.connect(self.update_fades)

    def update_fades(self, *_):
        bar = self.horizontalScrollBar()
        viewport = self.viewport().geometry()
        for fade, visible in (
            (self.left_fade, bar.value() > bar.minimum()),
            (self.right_fade, bar.value() < bar.maximum()),
        ):
            x = viewport.left() if fade.edge == Qt.LeftEdge else viewport.right() - fade.width() + 1
            fade.setGeometry(x, viewport.top(), fade.width(), viewport.height())
            fade.setVisible(visible)
            fade.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_fades()

    def add_button(self, button):
        # Insert before the trailing stretch so buttons stay left-aligned.
        self.row.insertWidget(self.row.count() - 1, button)
        self.updateGeometry()

    def fit_height(self, reference_button):
        """Size the strip for the *styled* buttons plus the thin scrollbar.

        Must run after the app stylesheet is applied: before that, buttons
        report their smaller unstyled height and the strip clips them.
        """
        buttons = [reference_button, *self.widget().findChildren(QPushButton)]
        for button in buttons:
            button.ensurePolished()
        button_height = max(button.sizeHint().height() for button in buttons)
        self.setFixedHeight(button_height + 12)

    def wheelEvent(self, event):
        # A normal (vertical) mouse wheel scrolls this row sideways.
        delta = event.angleDelta()
        step = delta.x() if abs(delta.x()) > abs(delta.y()) else delta.y()
        bar = self.horizontalScrollBar()
        bar.setValue(bar.value() - step)
        event.accept()

class UpdateRelay(QObject):
    """Carries update-check and download results from worker threads back to the UI thread."""
    checked = Signal(object)
    progress = Signal(int, int)
    finished = Signal(object)

NSFW_LABELS = {"hide": "NSFW: Hidden", "show": "NSFW: Shown", "only": "NSFW: Only"}
NSFW_CYCLE = {"hide": "show", "show": "only", "only": "hide"}

FILTER_TEXT_MAX = 150  # pixels of label text before a jewel name is shortened

def _filter_font():
    font = QFont(QApplication.font())
    font.setPixelSize(15)
    font.setWeight(QFont.Weight.ExtraBold)
    return font

def elided_filter_text(text):
    return QFontMetrics(_filter_font()).elidedText(text, Qt.ElideRight, FILTER_TEXT_MAX)

def filter_button_width(text):
    """Width that fits text in the checked filter style (15px, weight 800, 3px border)."""
    # 15px horizontal padding and 3px border on each side, plus a little slack.
    return QFontMetrics(_filter_font()).horizontalAdvance(text) + 2 * (15 + 3) + 10

class JewelLibrary(QMainWindow):
    def __init__(self, windowed=False):
        super().__init__()
        ensure_data_files()
        self.games = load_json(GAMES_FILE)
        self.drives = load_json(DRIVES_FILE)
        # An empty set means All; otherwise every selected jewel is shown.
        self.selected_drives = set()
        # NSFW protection: hidden by default every time the app starts.
        self.nsfw_mode = "hide"
        self.filter_buttons = {}
        self.setWindowTitle("SteamDeck Jewels")
        self.setWindowIcon(app_icon())
        self.resize(1280, 800)
        if not windowed:
            self.showFullScreen()

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28,20,28,20)

        top = QHBoxLayout()
        brand = QLabel("STEAMDECK JEWELS")
        brand.setObjectName("brand")
        top.addWidget(brand)
        top.addStretch()
        # Short connected-drive count; the full per-drive list is in its tooltip.
        self.drive_summary = QLabel()
        self.drive_summary.setObjectName("driveStatus")
        top.addWidget(self.drive_summary)
        top.addSpacing(12)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search games…")
        self.search.setFixedWidth(320)
        self.search.textChanged.connect(self.render)
        top.addWidget(self.search)
        # The everyday action stays visible; everything else lives in one menu.
        # Hidden until the startup check finds a newer release on GitHub.
        self.update_button = QPushButton("Update available")
        self.update_button.setObjectName("primaryAction")
        self.update_button.clicked.connect(lambda: self.offer_update(self.latest_release_tag))
        self.update_button.hide()
        top.addWidget(self.update_button)
        add_game = QPushButton("+ Add Game")
        add_game.setObjectName("primaryAction")
        add_game.clicked.connect(self.add_game)
        top.addWidget(add_game)
        manage = QPushButton("Manage ▾")
        manage_menu = QMenu(manage)
        manage_menu.addAction("Edit Game…", lambda: self.choose_game_to_edit())
        manage_menu.addAction("Remove Game…", lambda: self.choose_game_to_remove())
        manage_menu.addSeparator()
        manage_menu.addAction("Add Jewel Drive…", lambda: self.add_jewel_drive())
        manage_menu.addAction("Rescan Drives", lambda: self.render())
        manage_menu.addSeparator()
        manage_menu.addAction("Open SDJ Folder", lambda: self.open_library_folder())
        manage.setMenu(manage_menu)
        top.addWidget(manage)
        outer.addLayout(top)

        help_menu = self.menuBar().addMenu("Help")
        folder_action = QAction("Open SDJ Folder", self)
        folder_action.triggered.connect(self.open_library_folder)
        help_menu.addAction(folder_action)
        api_action = QAction("Set Up SteamGridDB API Key", self)
        api_action.triggered.connect(self.configure_steamgriddb)
        help_menu.addAction(api_action)
        appid_action = QAction("How to Find a Steam AppID", self)
        appid_action.triggered.connect(self.show_appid_help)
        help_menu.addAction(appid_action)
        help_menu.addSeparator()
        update_action = QAction("Check for Updates…", self)
        update_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(update_action)
        about_action = QAction("About SteamDeck Jewels", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        self.filters = QHBoxLayout()
        self.nsfw_filter = QPushButton()
        self.nsfw_filter.setObjectName("driveFilter")
        self.nsfw_filter.setCheckable(True)
        self.nsfw_filter.setToolTip("Click to cycle: NSFW hidden → shown → NSFW only")
        self.nsfw_filter.setMinimumWidth(max(
            filter_button_width(label) for label in NSFW_LABELS.values()
        ))
        self.nsfw_filter.clicked.connect(self.cycle_nsfw_filter)
        self.sync_nsfw_button()
        # "All" and NSFW stay pinned at the left; the jewel buttons live in a
        # horizontally scrolling strip so any number of drives fits.
        self.drive_strip = DriveStrip()
        self.rebuild_filters()
        # Top-align everything so the pinned buttons line up with the strip's
        # buttons whether or not its scrollbar is showing underneath them.
        self.filters.insertWidget(0, self.filter_buttons["All"], 0, Qt.AlignTop)
        self.filters.addWidget(self.nsfw_filter, 0, Qt.AlignTop)
        # The filter row holds only filters, so the drive strip gets nearly the
        # full width of the window.
        self.filters.addWidget(self.drive_strip, 1, Qt.AlignTop)
        outer.addLayout(self.filters)
        QApplication.instance().focusChanged.connect(self.keep_focused_filter_visible)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        # QAbstractScrollArea does not enable finger-drag scrolling by default.
        # Steam Deck touch input needs an explicit kinetic scroller on the viewport.
        QScroller.grabGesture(self.scroll.viewport(), QScroller.TouchGesture)
        # Qt's default wheel step (20px x 3 lines) crawls through tall cover cards;
        # this moves roughly half a card per wheel notch.
        self.scroll.verticalScrollBar().setSingleStep(55)
        self.scroll.viewport().installEventFilter(self)
        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        self.grid.setSpacing(16)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll, 1)

        esc = QAction(self)
        esc.setShortcut(QKeySequence("Esc"))
        esc.triggered.connect(self.showNormal)
        self.addAction(esc)

        self.setStyleSheet("""
        QMainWindow, QWidget { background:#0e0e16; color:#f5f3fa; font-family: Sans Serif; }
        #brand { font-size:28px; font-weight:800; letter-spacing:2px; padding:8px; }
        QLineEdit { background:#1a1925; border:2px solid #343047; border-radius:12px; padding:11px 14px; font-size:17px; }
        QPushButton { background:#211f2d; border:2px solid #343047; border-radius:12px; padding:9px 16px; font-size:15px; }
        QPushButton:hover, QPushButton:focus { border-color:#a883e8; background:#2a2638; }
        QPushButton:checked { background:#5d3f88; border-color:#c7a7ff; }
        QPushButton#primaryAction { background:#5d3f88; border-color:#8c62c7; font-weight:700; }
        QPushButton#primaryAction:hover, QPushButton#primaryAction:focus { background:#6e4c9f; border-color:#c7a7ff; }
        QPushButton::menu-indicator { width:0; image:none; }
        QMenu { background:#1a1925; border:2px solid #343047; border-radius:10px; padding:6px; }
        QMenu::item { padding:10px 28px 10px 18px; font-size:15px; border-radius:8px; color:#f5f3fa; }
        QMenu::item:selected { background:#5d3f88; }
        QMenu::separator { height:1px; background:#343047; margin:6px 10px; }
        QPushButton#driveFilter:checked,
        QPushButton#driveFilter:checked:hover,
        QPushButton#driveFilter:checked:focus {
            background:#8c62c7; border:3px solid #eadcff; color:#ffffff;
            font-weight:800; padding:8px 15px;
        }
        #card { background:#171621; border:2px solid #292638; border-radius:16px; }
        #card:hover, #card:focus { border:3px solid #b18cf2; background:#201d2c; }
        #title { font-size:15px; font-weight:700; background:transparent; }
        #driveStatus { color:#aaa4b9; font-size:12px; background:transparent; }
        #nsfw { color:#ffb0bd; font-weight:700; font-size:11px; background:transparent; }
        QScrollArea { background:transparent; }
        QScrollBar:vertical {
            background:#171621; width:28px; margin:28px 0 28px 0;
            border:1px solid #343047; border-radius:12px;
        }
        QScrollBar::handle:vertical {
            background:#72549e; min-height:48px; border-radius:11px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background:#2a2638; height:28px; border:1px solid #55496c;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:transparent; }
        #driveStrip QScrollBar:horizontal {
            background:#171621; height:10px; margin:0; border:none; border-radius:5px;
        }
        #driveStrip QScrollBar::handle:horizontal {
            background:#72549e; min-width:48px; border-radius:5px;
        }
        #driveStrip QScrollBar::add-line:horizontal, #driveStrip QScrollBar::sub-line:horizontal {
            width:0; border:none; background:transparent;
        }
        #driveStrip QScrollBar::add-page:horizontal, #driveStrip QScrollBar::sub-page:horizontal {
            background:transparent;
        }
        """)

        self.drive_strip.fit_height(self.filter_buttons["All"])
        self.latest_release_tag = ""
        self.update_relay = UpdateRelay()
        self.update_relay.checked.connect(self.on_background_update_check)
        self.render()
        # Report the outcome of an update that just finished, then quietly look for a newer one.
        QTimer.singleShot(0, self.show_update_result)
        QTimer.singleShot(2000, self.start_background_update_check)
        if not self.drives and not self.games:
            self.show_first_run_help()

    def rebuild_filters(self):
        self.filter_buttons.clear()
        self.filter_buttons["All"] = self.make_filter_button("All")
        for name in self.drives:
            self.filter_buttons[name] = self.make_filter_button(name)
            self.drive_strip.add_button(self.filter_buttons[name])
        self.sync_filter_buttons()

    def keep_focused_filter_visible(self, _old, new):
        """Scroll the drive strip so a controller/keyboard-focused jewel is on screen."""
        if new is not None and self.drive_strip.isAncestorOf(new):
            self.drive_strip.ensureWidgetVisible(new, 24, 0)

    def make_filter_button(self, name):
        # Long jewel names are shortened with "…" so one name cannot hog the row;
        # the full name is in the tooltip.
        label = elided_filter_text(name)
        button = QPushButton(label)
        button.setObjectName("driveFilter")
        button.setCheckable(True)
        if label != name:
            button.setToolTip(name)
        # Reserve room for the bold, thicker-bordered "selected" style so the
        # label is not clipped when the button is checked.
        button.setMinimumWidth(filter_button_width(label))
        button.clicked.connect(lambda checked, n=name: self.set_filter(n, checked))
        return button

    def add_jewel_drive(self):
        name, accepted = QInputDialog.getText(
            self, "Add Jewel Drive", "Jewel name (also used as its cover-folder name):"
        )
        name = name.strip()
        if not accepted or not name:
            return
        if name.casefold() in {existing.casefold() for existing in self.drives}:
            QMessageBox.information(self, "Jewel already exists", f"{name} is already configured.")
            return
        if cover_folder_name(name) != name:
            QMessageBox.warning(
                self, "Invalid jewel name",
                "Use a folder-safe name without < > : \" / \\ | ? * characters."
            )
            return

        label, accepted = QInputDialog.getText(
            self, "SD card label", "Volume label SteamOS/Windows will show:", text=name
        )
        label = label.strip()
        if not accepted or not label:
            return

        jewel_files = sorted(JEWELS.glob("*.svg"), key=lambda path: path.stem)
        jewel_names = [path.stem.replace("-", " ").title() for path in jewel_files]
        preferred = name.replace("-", " ").title()
        default_index = jewel_names.index(preferred) if preferred in jewel_names else 0
        jewel_name, accepted = QInputDialog.getItem(
            self, "Choose jewel icon", "Jewel artwork:", jewel_names, default_index, False
        )
        if not accepted:
            return
        jewel_file = jewel_files[jewel_names.index(jewel_name)]
        jewel_asset = f"assets/jewels/{jewel_file.name}"
        self.drives[name] = {
            "label": label,
            "volume_labels": list(dict.fromkeys([label, label.upper()])),
            "mount_candidates": [
                f"/run/media/deck/{label}",
                f"/run/media/deck/{label.upper()}",
            ],
            "jewel": jewel_asset,
        }
        try:
            # Reuse an existing folder if one was prepared before adding the drive.
            (COVERS / name).mkdir(parents=True, exist_ok=True)
            (COVERS / name / "NSFW").mkdir(parents=True, exist_ok=True)
            save_json(DRIVES_FILE, self.drives)
        except Exception as error:
            self.drives.pop(name, None)
            QMessageBox.critical(self, "Could not add drive", str(error))
            return

        # Insert the new filter before the stretch/add button area.
        self.filter_buttons[name] = self.make_filter_button(name)
        self.drive_strip.add_button(self.filter_buttons[name])
        # Scroll once the layout has placed the new button, or it has no position yet.
        new_button = self.filter_buttons[name]
        QTimer.singleShot(50, lambda: self.drive_strip.ensureWidgetVisible(new_button, 24, 0))
        self.sync_filter_buttons()
        self.render()
        QMessageBox.information(
            self, "Jewel drive added",
            f"Added {name}.\n\nCover folder:\n{COVERS / name}\n\n"
            f"Expected SD card label: {label}"
        )

    def add_game(self):
        if not self.drives:
            QMessageBox.information(
                self, "Add a Jewel Drive First",
                "Before adding a game, choose Manage ▾ → Add Jewel Drive and enter the name printed on your SD card."
            )
            return
        selected_drive = next(iter(self.selected_drives)) if len(self.selected_drives) == 1 else ""
        if not selected_drive:
            volumes = windows_volumes()
            connected = [name for name, info in self.drives.items() if find_drive(info, volumes)]
            if len(connected) == 1:
                selected_drive = connected[0]
        dialog = AddGameDialog(list(self.drives), selected_drive, self)
        while dialog.exec() == QDialog.Accepted:
            try:
                cover_source, cover_data, cover_suffix, source_description = self.resolve_cover(
                    dialog.cover_controls, dialog.title.text().strip()
                )
                game = add_game_to_library(
                    self.games,
                    self.drives,
                    dialog.title.text(),
                    dialog.drive.currentText(),
                    cover_source,
                    cover_data,
                    cover_suffix,
                    dialog.nsfw.isChecked(),
                )
            except CoverChoiceCancelled:
                continue
            except Exception as error:
                QMessageBox.warning(self, "Could not add game", str(error))
                continue
            self.selected_drives = {game["drive"]}
            self.reveal_if_nsfw(game)
            self.sync_filter_buttons()
            self.render()
            QMessageBox.information(
                self, "Game added",
                f"Added {game['title']} to {game['drive']}.\n\n"
                f"Cover source: {source_description}\n\n"
                f"Cover folder:\n{cover_directory(game)}"
            )
            break

    def resolve_cover(self, controls, title):
        """Return (source path, bytes, suffix, description); (None,)*4 keeps the current cover."""
        mode = controls.mode()
        if mode == COVER_KEEP:
            return None, None, None, None
        if mode == COVER_LOCAL:
            return controls.cover.text(), None, "", "Local image file"
        if mode == COVER_URL:
            data, suffix, description = fetch_cover_from_url(controls.cover.text().strip())
            return "", data, suffix, description
        appid = controls.cover.text().strip()
        description = f"Steam AppID {appid}"
        if mode == COVER_SEARCH:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                items = search_steam_results(title)
                picker = SteamResultDialog(title, items, self)
            finally:
                QApplication.restoreOverrideCursor()
            if picker.exec() != QDialog.Accepted:
                raise CoverChoiceCancelled()
            chosen = picker.chosen()
            appid = str(chosen["id"])
            description = f'Steam search: {chosen.get("name", title)} (AppID {appid})'
        data, suffix, fetched_from = fetch_cover_by_appid(appid)
        return "", data, suffix, f"{description}; artwork from {fetched_from}"

    def nsfw_allowed(self, game):
        if self.nsfw_mode == "hide":
            return not game.get("nsfw")
        if self.nsfw_mode == "only":
            return bool(game.get("nsfw"))
        return True

    def reveal_if_nsfw(self, game):
        """After adding/editing an NSFW game, make sure the user can see it."""
        if game.get("nsfw") and self.nsfw_mode == "hide":
            self.nsfw_mode = "show"
            self.sync_nsfw_button()

    def visible_games(self):
        return [
            game for game in self.games
            if not self.selected_drives or game["drive"] in self.selected_drives
            if self.nsfw_allowed(game)
        ]

    def choose_game_to_edit(self):
        visible_games = self.visible_games()
        if not visible_games:
            QMessageBox.information(self, "Edit Game", "There are no games in this view.")
            return
        labels = [f'{game["title"]} - {game["drive"]}' for game in visible_games]
        label, accepted = QInputDialog.getItem(
            self, "Edit Game", "Choose the library entry to edit:", labels, 0, False
        )
        if accepted:
            self.edit_game(visible_games[labels.index(label)])

    def portable_target(self, path, drive_name):
        path = path.strip()
        if not path or path.startswith("steam://") or "{drive}" in path:
            return path
        location = find_drive(self.drives[drive_name])
        if location:
            try:
                relative = Path(path).resolve().relative_to(Path(location).resolve())
                separator = "" if str(location).endswith(("/", "\\")) else "/"
                return "{drive}" + separator + relative.as_posix()
            except ValueError:
                pass
        return path

    def edit_game(self, game):
        dialog = EditGameDialog(game, list(self.drives), self)
        while dialog.exec() == QDialog.Accepted:
            title = dialog.title.text().strip()
            drive = dialog.drive.currentText()
            if not title:
                QMessageBox.warning(self, "Could not edit game", "Enter a game name.")
                continue
            if any(
                other is not game and other["drive"].casefold() == drive.casefold()
                and other["title"].casefold() == title.casefold()
                for other in self.games
            ):
                QMessageBox.warning(self, "Could not edit game", f"{title} already exists on {drive}.")
                continue
            try:
                # Fetch and validate the new cover before touching anything on disk.
                cover_source, cover_data, cover_suffix, _ = self.resolve_cover(
                    dialog.cover_controls, title
                )
                if cover_source is not None:
                    cover_data, cover_suffix = prepare_cover(cover_source, cover_data, cover_suffix)
            except CoverChoiceCancelled:
                continue
            except Exception as error:
                QMessageBox.warning(self, "Could not change cover", str(error))
                continue
            if self.apply_game_edit(game, dialog, title, drive, cover_data, cover_suffix):
                return

    def apply_game_edit(self, game, dialog, title, drive, cover_data, cover_suffix):
        old_values = dict(game)
        old_folder = cover_directory(game)
        game.update({"title": title, "drive": drive, "nsfw": dialog.nsfw.isChecked()})
        if cover_data is not None:
            game["cover"] = ""  # an explicit cover path would override the new image
        launch = dict(game.get("launch", {}))
        launch.update({
            "type": "path",
            "target": self.portable_target(dialog.executable.text(), drive),
            "working_directory": "",
        })
        launch.setdefault("arguments", [])
        game["launch"] = launch
        new_folder = cover_directory(game)
        moved = False
        try:
            if old_folder != new_folder and old_folder.is_dir():
                if new_folder.exists():
                    raise ValueError(f"The destination cover folder already exists:\n{new_folder}")
                new_folder.parent.mkdir(parents=True, exist_ok=True)
                old_folder.rename(new_folder)
                moved = True
            save_json(GAMES_FILE, self.games)
        except Exception as error:
            if moved and new_folder.is_dir() and not old_folder.exists():
                old_folder.parent.mkdir(parents=True, exist_ok=True)
                new_folder.rename(old_folder)
            game.clear()
            game.update(old_values)
            QMessageBox.warning(self, "Could not edit game", str(error))
            return False
        if cover_data is not None:
            try:
                replace_game_cover(game, cover_data, cover_suffix)
            except Exception as error:
                QMessageBox.warning(
                    self, "Cover not replaced",
                    f"The other changes were saved, but the new cover could not be written:\n{error}"
                )
        self.selected_drives = {drive}
        self.reveal_if_nsfw(game)
        self.sync_filter_buttons()
        self.render()
        return True

    def sync_filter_buttons(self):
        for name, button in self.filter_buttons.items():
            button.setChecked(not self.selected_drives if name == "All" else name in self.selected_drives)

    def set_filter(self, name, checked=True):
        if name == "All":
            self.selected_drives.clear()
        elif checked:
            self.selected_drives.add(name)
        else:
            self.selected_drives.discard(name)
        self.sync_filter_buttons()
        self.render()

    def cycle_nsfw_filter(self):
        self.nsfw_mode = NSFW_CYCLE[self.nsfw_mode]
        self.sync_nsfw_button()
        self.render()

    def sync_nsfw_button(self):
        self.nsfw_filter.setText(NSFW_LABELS[self.nsfw_mode])
        self.nsfw_filter.setChecked(self.nsfw_mode != "hide")

    def choose_game_to_remove(self):
        visible_games = self.visible_games()
        if not visible_games:
            QMessageBox.information(self, "Remove Game", "There are no games in this view.")
            return
        labels = [
            f'{game["title"]} — {game["drive"]}'
            + (" (NSFW)" if game.get("nsfw") else "")
            for game in visible_games
        ]
        label, accepted = QInputDialog.getItem(
            self, "Remove Game", "Choose the library entry to remove:", labels, 0, False
        )
        if accepted:
            self.remove_game(visible_games[labels.index(label)])

    def remove_game(self, game):
        folder = cover_directory(game)
        shared_cover = any(
            other is not game and cover_directory(other) == folder for other in self.games
        )
        prompt = QMessageBox(self)
        prompt.setWindowTitle("Remove Game")
        prompt.setIcon(QMessageBox.Warning)
        prompt.setText(f'Remove “{game["title"]}” from {game["drive"]}?')
        prompt.setInformativeText(
            "Choose whether to keep its cover folder. This does not uninstall the game from the SD card."
        )
        keep_button = prompt.addButton("Remove Entry Only", QMessageBox.AcceptRole)
        delete_button = prompt.addButton("Remove Entry and Cover", QMessageBox.DestructiveRole)
        cancel_button = prompt.addButton(QMessageBox.Cancel)
        if shared_cover:
            delete_button.setEnabled(False)
            delete_button.setToolTip("Another library entry uses this cover folder.")
        prompt.exec()
        clicked = prompt.clickedButton()
        if clicked == cancel_button or clicked not in (keep_button, delete_button):
            return
        try:
            remove_game_from_library(self.games, game, clicked == delete_button)
        except Exception as error:
            QMessageBox.warning(self, "Could not remove game", str(error))
            self.render()
            return
        self.render()
        QMessageBox.information(
            self,
            "Game removed",
            f'Removed {game["title"]} from {game["drive"]}.\n\n'
            + (f"Deleted cover folder:\n{folder}" if clicked == delete_button else f"Kept cover folder:\n{folder}"),
        )

    def open_library_folder(self):
        try:
            if os.name == "nt":
                os.startfile(str(USER_HOME))
            else:
                subprocess.Popen(["xdg-open", str(USER_HOME)])
        except Exception as error:
            QMessageBox.warning(self, "Could not open folder", str(error))

    def configure_steamgriddb(self):
        QMessageBox.information(
            self,
            "SteamGridDB API Key",
            "SteamGridDB is optional. It helps find cover artwork when Steam has no suitable image.\n\n"
            "1. Create or sign in to your account at steamgriddb.com.\n"
            "2. Open your account Preferences, then choose API.\n"
            "3. Click Create API Key and copy the key.\n"
            "4. Continue here and paste it into the next box.\n\n"
            "The key is stored only on this device, in your library folder, and updates keep it."
        )
        key, accepted = QInputDialog.getText(
            self, "Save SteamGridDB API Key", "Paste your API key:", QLineEdit.Password
        )
        key = key.strip()
        if not accepted:
            return
        if not key:
            QMessageBox.warning(self, "No Key Entered", "Nothing was saved.")
            return
        try:
            key_folder = SECRETS
            key_folder.mkdir(parents=True, exist_ok=True)
            key_file = key_folder / "steamgriddb.key"
            key_file.write_text(key + "\n", encoding="utf-8")
            if os.name != "nt":
                key_file.chmod(0o600)
        except Exception as error:
            QMessageBox.warning(self, "Could Not Save API Key", str(error))
            return
        QMessageBox.information(self, "API Key Saved", "SteamGridDB cover lookup is ready.")

    def show_update_result(self):
        result = updater.take_result(USER_HOME)
        if not result:
            return
        ok, message = result
        if ok:
            QMessageBox.information(self, "Update complete", message)
        else:
            QMessageBox.warning(self, "Update didn't finish", message)

    def start_background_update_check(self):
        def work():
            try:
                result = updater.check()
            except Exception:
                result = None  # offline, not configured, dev copy: stay quiet
            self.update_relay.checked.emit(result)
        threading.Thread(target=work, daemon=True).start()

    def on_background_update_check(self, result):
        if result and result[2]:
            self.latest_release_tag = result[1]
            # The button stays as a reminder if the user picks "Not Now".
            self.update_button.setText(f"Update to {result[1]}")
            self.update_button.show()
            self.prompt_startup_update()

    def prompt_startup_update(self):
        # Wait until any other dialog (first-run welcome, update result) is closed.
        if QApplication.activeModalWidget() is not None:
            QTimer.singleShot(1000, self.prompt_startup_update)
            return
        self.offer_update(self.latest_release_tag)

    def check_for_updates(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            current, tag, newer = updater.check()
        except Exception as error:
            QApplication.restoreOverrideCursor()
            QMessageBox.information(self, "Check for Updates", str(error))
            return
        QApplication.restoreOverrideCursor()
        if newer:
            self.offer_update(tag)
        else:
            QMessageBox.information(
                self, "Check for Updates", f"You have the latest version ({current})."
            )

    def offer_update(self, tag):
        current = updater.current_version()
        prompt = QMessageBox(self)
        prompt.setWindowTitle("Update available")
        prompt.setIcon(QMessageBox.Information)
        prompt.setText(f"A new version of SteamDeck Jewels is available: {tag.lstrip('v')}")
        prompt.setInformativeText(
            f"You have {current}. If you update now, SteamDeck Jewels will close, install the "
            "update and reopen by itself. Your games, drives, covers and API key are kept."
        )
        update_now = prompt.addButton("Update Now", QMessageBox.AcceptRole)
        later = prompt.addButton("Not Now", QMessageBox.RejectRole)
        prompt.setDefaultButton(update_now)
        prompt.setEscapeButton(later)
        prompt.exec()
        if prompt.clickedButton() is not update_now:
            return
        self.run_update()

    def run_update(self):
        """Download the update with a progress bar, then hand over to it and close."""
        progress = QProgressDialog("Downloading the update…", "", 0, 100, self)
        progress.setWindowTitle("Updating SteamDeck Jewels")
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def on_progress(done, total):
            if total:
                progress.setValue(int(done * 100 / total))

        def on_finished(error):
            progress.close()
            if error is not None:
                QMessageBox.warning(self, "Update", str(error))
                return
            QApplication.quit()  # the new version starts by itself

        self.update_relay.progress.connect(on_progress)
        self.update_relay.finished.connect(on_finished)

        def work():
            try:
                updater.install(USER_HOME, lambda done, total: self.update_relay.progress.emit(done, total))
                error = None
            except Exception as exc:  # report every failure in the dialog
                error = exc if isinstance(exc, updater.UpdateError) else updater.UpdateError(
                    f"The update failed: {exc}")
            self.update_relay.finished.emit(error)
        threading.Thread(target=work, daemon=True).start()

    def show_about(self):
        QMessageBox.information(
            self, "About SteamDeck Jewels",
            f"SteamDeck Jewels {updater.current_version()}\n\n"
            "A controller-friendly library for games spread across SD cards.\n"
            "MIT License."
            + (f"\n\nhttps://github.com/{updater.configured_repo()}" if updater.configured_repo() else "")
        )

    def show_appid_help(self):
        QMessageBox.information(
            self,
            "Finding a Steam AppID",
            "Open the game's Steam Store page and look at its address.\n\n"
            "Example:\nhttps://store.steampowered.com/app/105600/Terraria/\n\n"
            "The number after /app/ is the AppID. In this example it is 105600.\n\n"
            "You can also choose ‘Search Steam by game name’ in Add Game and let SDJ find it for you."
        )

    def show_first_run_help(self):
        QMessageBox.information(
            self,
            "Welcome to SteamDeck Jewels",
            "Your library starts empty—this package contains no one else’s games or personal data.\n\n"
            "Start here:\n"
            "1. Choose Manage ▾ → Add Jewel Drive.\n"
            "2. Enter the name printed on your SD card and choose a gem.\n"
            "3. Choose + Add Game and select that jewel drive.\n"
            "4. Let SDJ search Steam for the cover, enter a Steam AppID, or choose your own image.\n\n"
            "SteamGridDB is optional. Set it up later from Help → Set Up SteamGridDB API Key."
        )

    def grid_columns(self):
        """How many cards fit across the visible grid area."""
        margins = self.grid.contentsMargins()
        available = self.scroll.viewport().width() - margins.left() - margins.right()
        card_step = GameCard.WIDTH + self.grid.horizontalSpacing()
        return max(1, (available + self.grid.horizontalSpacing()) // card_step)

    def place_cards(self):
        cols = self.grid_columns()
        self.grid_cols = cols
        for i, card in enumerate(self.cards):
            self.grid.addWidget(card, i // cols, i % cols)

    def eventFilter(self, watched, event):
        # Re-flow the existing cards whenever the grid area's width changes how
        # many fit (window resize, maximize, fullscreen, scrollbar appearing).
        if (
            event.type() == QEvent.Resize
            and watched is self.scroll.viewport()
            and getattr(self, "cards", None)
            and self.grid_columns() != getattr(self, "grid_cols", None)
        ):
            for card in self.cards:
                self.grid.removeWidget(card)
            self.place_cards()
        return super().eventFilter(watched, event)

    def clear_grid(self):
        self.cards = []
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def render(self):
        self.clear_grid()
        volumes = windows_volumes()
        drive_locations = {
            name: find_drive(info, volumes) for name, info in self.drives.items()
        }
        connected = sum(1 for location in drive_locations.values() if location)
        self.drive_summary.setText(
            f"{connected} of {len(drive_locations)} drives connected"
            if drive_locations else "No jewel drives yet"
        )
        self.drive_summary.setToolTip("\n".join(
            f"{name}: {location or 'Offline'}"
            for name, location in drive_locations.items()
        ))
        q = self.search.text().strip().casefold()
        items = []
        for g in self.games:
            if self.selected_drives and g["drive"] not in self.selected_drives:
                continue
            if not self.nsfw_allowed(g):
                continue
            if q and q not in g["title"].casefold():
                continue
            items.append(g)

        self.cards = [
            GameCard(
                g, self.drives[g["drive"]], drive_locations[g["drive"]],
                self.launch_game, self.edit_game, self.remove_game
            )
            for g in items
        ]
        self.place_cards()

    def launch_game(self, game):
        launch = game.get("launch", {})
        target = launch.get("target", "").strip()
        if not target:
            start = find_drive(self.drives[game["drive"]]) or ""
            target, _ = QFileDialog.getOpenFileName(
                self, f'Choose {game["title"]} executable', start,
                "Windows executables (*.exe);;All files (*)"
            )
            if not target:
                return
            launch = dict(launch)
            launch.update({
                "type": "path", "target": self.portable_target(target, game["drive"]),
                "working_directory": "", "arguments": launch.get("arguments", []),
            })
            game["launch"] = launch
            try:
                save_json(GAMES_FILE, self.games)
            except Exception as error:
                QMessageBox.warning(self, "Could not save executable", str(error))
                return
            target = launch["target"]

        drive_location = find_drive(self.drives[game["drive"]])
        if "{drive}" in target:
            if not drive_location:
                QMessageBox.warning(
                    self, "Drive offline", f'{game["drive"]} is not currently connected.'
                )
                return
            target = target.replace("{drive}", drive_location)

        if target.startswith("steam://"):
            if os.name == "nt":
                os.startfile(target)
            else:
                subprocess.Popen(["xdg-open", target])
            return

        target_path = Path(os.path.expanduser(target))
        if not target_path.exists():
            QMessageBox.warning(self, "Game not found", f"Launch target does not exist:\n{target_path}")
            return

        args = launch.get("arguments", [])
        cwd = launch.get("working_directory", "").strip() or str(target_path.parent)
        try:
            if target_path.suffix.lower() == ".exe":
                if os.name == "nt":
                    subprocess.Popen([str(target_path), *args], cwd=cwd)
                else:
                    # Prefer Steam shortcuts for Windows games. Wine is fallback only.
                    wine = shutil.which("wine")
                    if not wine:
                        QMessageBox.warning(
                            self, "Windows game",
                            "Configure this title as a Steam shortcut and use a steam:// "
                            "launch target, or install Wine for direct launching."
                        )
                        return
                    subprocess.Popen([wine, str(target_path), *args], cwd=cwd)
            else:
                subprocess.Popen([str(target_path), *args], cwd=cwd)
        except Exception as e:
            QMessageBox.critical(self, "Launch failed", str(e))

def running_on_steamos():
    try:
        return re.search(r'^ID="?steamos', Path("/etc/os-release").read_text(encoding="utf-8"), re.M) is not None
    except OSError:
        return False

def install_desktop_entry():
    """Give the AppImage a menu entry and icon, pointing at wherever the file is now."""
    try:
        appimage = os.environ["APPIMAGE"]
        icon = USER_HOME / "steamdeck-jewels.svg"
        USER_HOME.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(JEWELS / "steamdeck-jewels-rainbow.svg", icon)
        applications = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "applications"
        applications.mkdir(parents=True, exist_ok=True)
        (applications / "SteamDeckJewels.desktop").write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=SteamDeck Jewels\n"
            "Comment=Controller-friendly game library for SD-card collections\n"
            f'Exec="{appimage}"\n'
            f"Icon={icon}\n"
            "Terminal=false\n"
            "Categories=Game;\n",
            encoding="utf-8",
        )
    except Exception:
        pass  # a missing menu entry must never stop the app from starting

def app_icon():
    """The rainbow jewel: the multi-size .ico on Windows, the SVG elsewhere."""
    jewels = JEWELS
    ico = jewels / "steamdeck-jewels-rainbow.ico"
    if os.name == "nt" and ico.is_file():
        return QIcon(str(ico))
    return QIcon(str(jewels / "steamdeck-jewels-rainbow.svg"))

def main():
    parser = argparse.ArgumentParser(description="Jewel drive game library")
    parser.add_argument("--windowed", action="store_true", help="run in a resizable window")
    parser.add_argument("--fullscreen", action="store_true", help="run fullscreen")
    parser.add_argument("--self-test", action="store_true", help="check the build starts, then exit")
    args, _ = parser.parse_known_args()  # ignore extra arguments added by launchers
    if os.name == "nt":
        # Without its own app ID, Windows groups the window under pythonw.exe and the
        # taskbar shows the Python logo instead of the jewel.
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SteamDeckJewels.Library")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName("SteamDeck Jewels")
    # Matches SteamDeckJewels.desktop so SteamOS/KDE shows the jewel for this window too.
    app.setDesktopFileName("SteamDeckJewels")
    app.setWindowIcon(app_icon())
    if args.self_test:
        # Used by the release build: Qt loads, bundled icons render, then exit without a window.
        problems = [str(p) for p in (JEWELS / "steamdeck-jewels-rainbow.svg", PLACEHOLDER_COVER) if not p.is_file()]
        if QPixmap(str(JEWELS / "ruby.svg")).isNull():
            problems.append("SVG icons can't be drawn (Qt SVG support missing)")
        print("self-test:", "OK " + updater.current_version() if not problems else "FAILED " + "; ".join(problems))
        return 1 if problems else 0
    # Fullscreen on the Steam Deck (Desktop and Gaming Mode); a normal window everywhere else.
    fullscreen = args.fullscreen or (running_on_steamos() and not args.windowed)
    if getattr(sys, "frozen", False) and os.environ.get("APPIMAGE"):
        install_desktop_entry()
    win = JewelLibrary(windowed=not fullscreen)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
