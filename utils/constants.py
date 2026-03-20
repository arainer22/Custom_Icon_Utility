"""
IconForge global constants and paths.

All paths that touch user data live under the current user's profile so the
app never writes inside Program Files or the repo checkout itself.
"""

from __future__ import annotations

import os
import sys
import tempfile

__version__ = "1.0.1"
APP_NAME = "IconForge"

# When built with PyInstaller --onefile the real files are extracted to a temp
# folder whose path is stored in sys._MEIPASS. We need this so bundled assets
# can be located at runtime.
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")

APPDATA_ROOT = os.getenv("APPDATA")
if APPDATA_ROOT:
    APP_DATA_DIR = os.path.join(APPDATA_ROOT, APP_NAME)
else:
    APP_DATA_DIR = os.path.join(
        os.path.expanduser("~"), "AppData", "Roaming", APP_NAME
    )

ICONS_DIR = os.path.join(APP_DATA_DIR, "icons")
CONFIG_PATH = os.path.join(APP_DATA_DIR, "config.json")
MANIFEST_PATH = os.path.join(APP_DATA_DIR, "manifest.json")
LOG_PATH = os.path.join(APP_DATA_DIR, "app.log")

ICONFORGE_ICO_PATH = os.path.join(ASSETS_DIR, "iconforge.ico")
BLANK_ICO_PATH = os.path.join(ASSETS_DIR, "blank.ico")

SHELL_ICON_REG_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons"
SHELL_ICON_VALUE_NAME = "29"

IMAGE_FILETYPES = [
    ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.ico *.webp"),
    ("All files", "*.*"),
]
LNK_FILETYPES = [
    ("Shortcuts", "*.lnk"),
    ("All files", "*.*"),
]

ICO_SIZES = [(16, 16), (32, 32), (48, 48), (256, 256)]

TEMP_BATCH_PATH = os.path.join(
    APP_DATA_DIR if APP_DATA_DIR else tempfile.gettempdir(),
    "IconForge_last_batch.json",
)
