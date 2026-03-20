"""
IconForge desktop refresh utilities.

After changing shortcut icons or registry keys, Windows caches should be
nudged so the changes appear promptly.
"""

from __future__ import annotations

import ctypes
import logging

log = logging.getLogger(__name__)

SHCNE_ASSOCCHANGED = 0x08000000
SHCNF_IDLIST = 0x0000



def refresh_desktop() -> None:
    """Force Windows to reload desktop icon associations on a best-effort basis."""
    try:
        shell32 = ctypes.windll.shell32
        shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
        log.info("Desktop refresh completed")
    except Exception as exc:
        log.error("Failed to refresh desktop icons: %s", exc)
        raise
