# -*- mode: python ; coding: utf-8 -*-
# PyInstaller recipe for the Windows installer and the Linux AppImage.
# Only the gem icons and the placeholder cover are bundled; the user's library lives elsewhere.
import sys

a = Analysis(
    ['packaging/launcher.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('assets/jewels', 'assets/jewels'),
        ('assets/covers/_placeholder.svg', 'assets/covers'),
    ],
    hiddenimports=['steamdeck_jewels.updater', 'PySide6.QtSvg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SteamDeckJewels',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/jewels/steamdeck-jewels-rainbow.ico' if sys.platform == 'win32' else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SteamDeckJewels',
)
