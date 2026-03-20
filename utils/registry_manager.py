"""
IconForge Windows registry helpers for the "Hide shortcut arrows" feature.

These functions only touch a single Explorer key and are reversible.
Administrator privileges are required to write to HKLM.
"""

from __future__ import annotations

import logging
import os
import winreg

from utils.constants import SHELL_ICON_REG_PATH, SHELL_ICON_VALUE_NAME

log = logging.getLogger(__name__)


def set_shell_icon_key(blank_ico_path: str) -> None:
    """Point the shortcut overlay icon to a transparent .ico file."""
    if not os.path.isfile(blank_ico_path):
        raise FileNotFoundError(f"Blank icon file not found: {blank_ico_path}")

    try:
        with winreg.CreateKeyEx(
            winreg.HKEY_LOCAL_MACHINE,
            SHELL_ICON_REG_PATH,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY,
        ) as key:
            winreg.SetValueEx(key, SHELL_ICON_VALUE_NAME, 0, winreg.REG_SZ, blank_ico_path)
        log.info("Shell icon key set to %s", blank_ico_path)
    except PermissionError:
        log.warning("Admin required to modify HKLM registry key")
        raise
    except OSError as exc:
        log.error("Failed to set shell icon key: %s", exc)
        raise


def delete_shell_icon_key() -> None:
    """Remove the custom overlay icon and restore the default shortcut arrow."""
    try:
        with winreg.OpenKeyEx(
            winreg.HKEY_LOCAL_MACHINE,
            SHELL_ICON_REG_PATH,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY,
        ) as key:
            winreg.DeleteValue(key, SHELL_ICON_VALUE_NAME)
        log.info("Shell icon key deleted; default arrows restored")
    except FileNotFoundError:
        log.info("Shell icon key already absent; nothing to restore")
    except PermissionError:
        log.warning("Admin required to modify HKLM registry key")
        raise
    except OSError as exc:
        log.error("Failed to delete shell icon key: %s", exc)
        raise
