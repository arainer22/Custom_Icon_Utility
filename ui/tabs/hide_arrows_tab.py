"""
IconForge "Hide Shortcut Arrows" tab.

Provides controls to replace the default shortcut overlay arrow with a
transparent icon and to restore the default arrow.
"""

from __future__ import annotations

import logging

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from utils.constants import BLANK_ICO_PATH
from utils.refresh import refresh_desktop
from utils.registry_manager import delete_shell_icon_key, set_shell_icon_key

log = logging.getLogger(__name__)


class HideArrowsTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        row = 0

        warning = ctk.CTkLabel(
            self,
            text=(
                "These operations modify the Windows registry (HKLM).\n"
                "Administrator privileges are required. Changes take effect\n"
                "after an Explorer restart or the next logon."
            ),
            font=ctk.CTkFont(size=13),
            text_color=("orange3", "orange"),
            justify="center",
        )
        warning.grid(row=row, column=0, padx=24, pady=(32, 24))
        row += 1

        ctk.CTkButton(
            self,
            text="Hide All Shortcut Arrows",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            fg_color=("dodgerblue", "#1a6dd4"),
            command=self._hide_arrows,
        ).grid(row=row, column=0, padx=80, pady=8, sticky="ew")
        row += 1

        ctk.CTkButton(
            self,
            text="Restore Default Arrows",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            fg_color=("gray55", "gray35"),
            command=self._restore_arrows,
        ).grid(row=row, column=0, padx=80, pady=8, sticky="ew")
        row += 1

        self.grid_rowconfigure(row, weight=1)

    def _hide_arrows(self) -> None:
        try:
            set_shell_icon_key(BLANK_ICO_PATH)
            refresh_desktop()
            CTkMessagebox(
                title="Done",
                message=(
                    "Shortcut arrows have been hidden.\n"
                    "You may need to restart Explorer or log out and back in "
                    "for full effect."
                ),
                icon="check",
            )
        except PermissionError:
            CTkMessagebox(
                title="Admin Required",
                message="Restart IconForge as Administrator to modify registry keys.",
                icon="cancel",
            )
        except FileNotFoundError as exc:
            log.error("Hide arrows failed: %s", exc)
            CTkMessagebox(title="Missing Asset", message=str(exc), icon="cancel")
        except Exception as exc:
            log.error("Hide arrows failed: %s", exc)
            CTkMessagebox(title="Error", message=str(exc), icon="cancel")

    def _restore_arrows(self) -> None:
        try:
            delete_shell_icon_key()
            refresh_desktop()
            CTkMessagebox(
                title="Done",
                message="Default shortcut arrows have been restored.",
                icon="check",
            )
        except PermissionError:
            CTkMessagebox(
                title="Admin Required",
                message="Restart IconForge as Administrator to modify registry keys.",
                icon="cancel",
            )
        except Exception as exc:
            log.error("Restore arrows failed: %s", exc)
            CTkMessagebox(title="Error", message=str(exc), icon="cancel")
