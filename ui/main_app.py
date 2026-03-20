"""
IconForge main application window.

Hosts the CTkTabview with three tabs: Change Icon, Hide Arrows, and
Utilities. Also shows an admin banner when the app is not running elevated.
"""

from __future__ import annotations

import ctypes
import json
import logging
import os
import subprocess
import sys

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from utils.config_manager import AppConfig
from utils.constants import APP_NAME, ICONFORGE_ICO_PATH, ICONS_DIR, TEMP_BATCH_PATH, __version__

log = logging.getLogger(__name__)


def is_admin() -> bool:
    """Return True if the current process has administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _write_json_atomic(path: str, payload: dict[str, object]) -> None:
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    os.replace(temp_path, path)


class IconForgeApp:
    """Top-level application controller."""

    def __init__(self, root, config: AppConfig | None = None):
        self.root = root
        self.config = config or AppConfig.load()
        self.session_modified_shortcuts: set[str] = set()

        self.root.title(f"{APP_NAME}  v{__version__}")
        self.root.geometry("920x720")
        self.root.minsize(720, 560)

        if os.path.isfile(ICONFORGE_ICO_PATH):
            try:
                self.root.iconbitmap(ICONFORGE_ICO_PATH)
            except Exception as exc:
                log.warning("Could not set window icon from %s: %s", ICONFORGE_ICO_PATH, exc)

        os.makedirs(ICONS_DIR, exist_ok=True)

        self._admin_banner: ctk.CTkFrame | None = None
        if not is_admin():
            self._show_admin_banner()

        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        from ui.tabs.change_icon_tab import ChangeIconTab
        from ui.tabs.hide_arrows_tab import HideArrowsTab
        from ui.tabs.utilities_tab import UtilitiesTab

        tab_change = self.tabview.add("Change Icon")
        tab_arrows = self.tabview.add("Hide Arrows")
        tab_utils = self.tabview.add("Utilities")

        self.change_icon_tab = ChangeIconTab(tab_change, app=self)
        self.change_icon_tab.pack(fill="both", expand=True)

        self.hide_arrows_tab = HideArrowsTab(tab_arrows)
        self.hide_arrows_tab.pack(fill="both", expand=True)

        self.utilities_tab = UtilitiesTab(tab_utils, app=self)
        self.utilities_tab.pack(fill="both", expand=True)

        self._try_restore_batch()

    def _show_admin_banner(self) -> None:
        self._admin_banner = ctk.CTkFrame(
            self.root, fg_color=("orange", "#7a4400"), corner_radius=8, height=36
        )
        self._admin_banner.pack(fill="x", padx=12, pady=(8, 0))

        ctk.CTkLabel(
            self._admin_banner,
            text="Running without admin privileges - some features may be limited.",
            font=ctk.CTkFont(size=12),
            text_color="white",
        ).pack(side="left", padx=12, pady=6)

        ctk.CTkButton(
            self._admin_banner,
            text="Restart as Admin",
            width=130,
            height=28,
            command=self._restart_as_admin,
        ).pack(side="right", padx=12, pady=6)

    def _restart_as_admin(self) -> None:
        """Re-launch the current process with UAC elevation."""
        try:
            os.makedirs(os.path.dirname(TEMP_BATCH_PATH), exist_ok=True)
            payload = {
                "batch": [
                    {
                        "lnk_path": shortcut.lnk_path,
                        "target": shortcut.target or "",
                        "original_name": shortcut.original_name or "",
                    }
                    for shortcut in self.change_icon_tab.batch
                ],
                "session_modified_shortcuts": sorted(self.session_modified_shortcuts),
            }
            _write_json_atomic(TEMP_BATCH_PATH, payload)
        except Exception as exc:
            log.warning("Could not persist state before UAC restart: %s", exc)

        if getattr(sys, "frozen", False):
            exe = sys.executable
            argv = sys.argv[1:]
        else:
            script_path = os.path.abspath(sys.argv[0])
            pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            exe = pythonw_path if os.path.isfile(pythonw_path) else sys.executable
            argv = [script_path, *sys.argv[1:]]

        params = subprocess.list2cmdline(argv)
        try:
            result = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
            if result <= 32:
                raise OSError(f"ShellExecuteW failed with code {result}")
            self.root.destroy()
        except Exception as exc:
            log.error("UAC elevation failed: %s", exc)
            CTkMessagebox(
                title="Elevation Failed",
                message=f"Could not restart IconForge with administrator privileges:\n{exc}",
                icon="cancel",
            )

    def _try_restore_batch(self) -> None:
        """Reload state saved before a UAC restart."""
        if not os.path.isfile(TEMP_BATCH_PATH):
            return

        try:
            with open(TEMP_BATCH_PATH, encoding="utf-8") as handle:
                data = json.load(handle)
            os.remove(TEMP_BATCH_PATH)

            batch_data = data
            session_paths: list[str] = []

            if isinstance(data, dict):
                batch_data = data.get("batch", [])
                raw_session_paths = data.get("session_modified_shortcuts", [])
                if isinstance(raw_session_paths, list):
                    session_paths = [path for path in raw_session_paths if isinstance(path, str)]

            if not isinstance(batch_data, list):
                raise TypeError("batch restore payload must be a list")

            from utils.icon_converter import extract_preview_png
            from utils.shortcut_handler import read_shortcut

            self.session_modified_shortcuts = set(session_paths)

            for entry in batch_data:
                if not isinstance(entry, dict) or "lnk_path" not in entry:
                    continue
                info = read_shortcut(entry["lnk_path"])
                source = info.current_icon or info.target
                if source and os.path.isfile(source):
                    info.icon_preview_bytes = extract_preview_png(source)
                self.change_icon_tab.batch.append(info)
                self.change_icon_tab._batch_paths.add(
                    os.path.normcase(os.path.abspath(entry["lnk_path"]))
                )

            self.change_icon_tab.batch_list.populate(self.change_icon_tab.batch)
            self.change_icon_tab._update_apply_state()
            self.utilities_tab.refresh_restore_buttons()
            log.info(
                "Restored %d shortcuts and %d session entries after UAC restart",
                len(self.change_icon_tab.batch),
                len(self.session_modified_shortcuts),
            )
        except Exception as exc:
            log.warning("Could not restore batch after UAC restart: %s", exc)

    def mainloop(self) -> None:
        self.root.mainloop()
