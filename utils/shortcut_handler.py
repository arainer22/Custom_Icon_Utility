"""
IconForge Windows .lnk shortcut reader and writer.

Uses pywin32's win32com.client to manipulate IShellLink objects.
"""

from __future__ import annotations

import logging
import os
import shutil
from contextlib import contextmanager

import pythoncom
import pywintypes
import win32com.client

from utils.models import ShortcutInfo

log = logging.getLogger(__name__)


@contextmanager
def _shell_link(lnk_path: str):
    """Yield a loaded WScript.Shell shortcut object with balanced COM init."""
    pythoncom.CoInitialize()
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        yield shell.CreateShortCut(lnk_path)
    finally:
        pythoncom.CoUninitialize()


def read_shortcut(lnk_path: str) -> ShortcutInfo:
    """
    Read metadata from a .lnk file and return a ShortcutInfo.

    Handles non-.exe targets like folders and URLs gracefully.
    """
    try:
        with _shell_link(lnk_path) as shortcut:
            target = shortcut.TargetPath or ""
            icon_loc = shortcut.IconLocation or ","

        icon_path = icon_loc.rsplit(",", 1)[0].strip() or None
        return ShortcutInfo(
            lnk_path=lnk_path,
            target=target,
            icon_location=icon_loc.strip() or None,
            current_icon=icon_path,
            original_name=os.path.basename(lnk_path),
        )
    except pywintypes.com_error as exc:
        log.error("COM failed while reading shortcut %s: %s", lnk_path, exc)
    except Exception as exc:
        log.error("Failed to read shortcut %s: %s", lnk_path, exc)

    return ShortcutInfo(
        lnk_path=lnk_path,
        target="",
        icon_location=None,
        current_icon=None,
        original_name=os.path.basename(lnk_path),
    )


def update_icon(lnk_path: str, ico_path: str) -> None:
    """
    Set the icon of a .lnk to *ico_path*.

    Raises FileNotFoundError if the icon is missing and PermissionError if the
    shortcut is protected.
    """
    if not os.path.isfile(lnk_path):
        raise FileNotFoundError(f"Shortcut not found: {lnk_path}")
    if not os.path.isfile(ico_path):
        raise FileNotFoundError(f"Icon file not found: {ico_path}")

    try:
        with _shell_link(lnk_path) as shortcut:
            shortcut.IconLocation = f"{ico_path},0"
            shortcut.Save()
        log.info("Icon updated: %s -> %s", lnk_path, ico_path)
    except PermissionError:
        log.warning("Permission denied updating %s", lnk_path)
        raise
    except pywintypes.com_error as exc:
        log.error("COM failed while updating icon for %s: %s", lnk_path, exc)
        raise
    except Exception as exc:
        log.error("Failed to update icon for %s: %s", lnk_path, exc)
        raise


def set_icon_location(lnk_path: str, icon_location: str) -> None:
    """Restore an exact shortcut IconLocation value, including any icon index."""
    if not os.path.isfile(lnk_path):
        raise FileNotFoundError(f"Shortcut not found: {lnk_path}")

    try:
        with _shell_link(lnk_path) as shortcut:
            shortcut.IconLocation = icon_location
            shortcut.Save()
        log.info("Icon location restored: %s -> %s", lnk_path, icon_location)
    except PermissionError:
        log.warning("Permission denied updating %s", lnk_path)
        raise
    except pywintypes.com_error as exc:
        log.error("COM failed while restoring icon location for %s: %s", lnk_path, exc)
        raise
    except Exception as exc:
        log.error("Failed to restore icon location for %s: %s", lnk_path, exc)
        raise


def clear_icon_override(lnk_path: str) -> None:
    """Clear a custom icon override so the shortcut falls back to its default icon."""
    if not os.path.isfile(lnk_path):
        raise FileNotFoundError(f"Shortcut not found: {lnk_path}")

    try:
        with _shell_link(lnk_path) as shortcut:
            shortcut.IconLocation = ""
            shortcut.Save()
        log.info("Cleared icon override for %s", lnk_path)
    except PermissionError:
        log.warning("Permission denied updating %s", lnk_path)
        raise
    except pywintypes.com_error as exc:
        log.error("COM failed while clearing icon override for %s: %s", lnk_path, exc)
        raise
    except Exception as exc:
        log.error("Failed to clear icon override for %s: %s", lnk_path, exc)
        raise


def rename_lnk_for_invisible_label(lnk_path: str, index: int) -> str:
    """
    Rename a .lnk so its display label becomes invisible on the desktop.

    Each shortcut receives a unique sequence of non-breaking spaces so Windows
    does not complain about duplicate names.
    """
    if not os.path.isfile(lnk_path):
        raise FileNotFoundError(f"Shortcut not found: {lnk_path}")

    directory = os.path.dirname(lnk_path)
    count = index + 1
    while True:
        invisible_name = "\u00A0" * count + ".lnk"
        new_path = os.path.join(directory, invisible_name)
        if not os.path.exists(new_path) or os.path.normcase(new_path) == os.path.normcase(lnk_path):
            break
        count += 1

    try:
        shutil.move(lnk_path, new_path)
        log.info("Renamed %s -> %s (invisible label #%d)", lnk_path, new_path, index)
        return new_path
    except PermissionError:
        log.warning("Permission denied renaming %s", lnk_path)
        raise
    except Exception as exc:
        log.error("Failed to rename %s: %s", lnk_path, exc)
        raise


def restore_original_name(lnk_path: str, original_name: str) -> str:
    """Rename a shortcut back to its original filename and return the new path."""
    if not os.path.isfile(lnk_path):
        raise FileNotFoundError(f"Shortcut not found: {lnk_path}")

    directory = os.path.dirname(lnk_path)
    restored_path = os.path.join(directory, original_name)

    try:
        shutil.move(lnk_path, restored_path)
        log.info("Restored name: %s -> %s", lnk_path, restored_path)
        return restored_path
    except Exception as exc:
        log.error("Failed to restore name for %s: %s", lnk_path, exc)
        raise
