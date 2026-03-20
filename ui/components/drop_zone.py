"""
IconForge drag-and-drop zone widget.

Supports tkinterdnd2 DND_FILES drag and drop and a Browse button fallback.
"""

from __future__ import annotations

import logging
import re
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from utils.constants import IMAGE_FILETYPES, LNK_FILETYPES

log = logging.getLogger(__name__)


class DropZone(ctk.CTkFrame):
    """A large drop-target area with a label and Browse button."""

    def __init__(
        self,
        master,
        accept: str = "lnk",
        on_files: Callable[[list[str]], None] | None = None,
        label_text: str | None = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.accept = accept
        self.on_files = on_files

        self.configure(
            corner_radius=12,
            border_width=2,
            border_color=("gray70", "gray30"),
            fg_color=("gray92", "gray17"),
        )

        default_text = (
            "Drag and drop .lnk shortcut(s) here\nor click Browse"
            if accept == "lnk"
            else "Drag and drop a new image here\n(PNG / JPG / ICO / etc.)"
        )

        self.label = ctk.CTkLabel(
            self,
            text=label_text or default_text,
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60"),
        )
        self.label.pack(expand=True, fill="both", padx=20, pady=(20, 5))

        filetypes = LNK_FILETYPES if accept == "lnk" else IMAGE_FILETYPES
        self.browse_btn = ctk.CTkButton(
            self,
            text="Browse...",
            width=120,
            command=lambda: self._browse(filetypes),
        )
        self.browse_btn.pack(pady=(0, 20))

        try:
            self.drop_target_register("DND_Files")
            self.dnd_bind("<<Drop>>", self._on_drop)
            self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.dnd_bind("<<DragLeave>>", self._on_drag_leave)
        except Exception:
            log.debug("tkinterdnd2 drag-and-drop is not available; browse-only mode")
            if not label_text:
                self.label.configure(text="Drag-and-drop unavailable - use Browse below")

    @staticmethod
    def _parse_dnd_data(data: str) -> list[str]:
        """Parse the space-separated, brace-quoted DND_Files string."""
        paths: list[str] = []
        for match in re.finditer(r"\{([^}]+)\}|(\S+)", data):
            path = match.group(1) or match.group(2)
            if path:
                paths.append(path)
        return paths

    def _on_drop(self, event) -> None:
        try:
            paths = self._parse_dnd_data(event.data)
            if self.accept == "lnk":
                filtered = [path for path in paths if path.lower().endswith(".lnk")]
            else:
                image_exts = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".ico", ".webp")
                filtered = [path for path in paths if path.lower().endswith(image_exts)]

            if filtered and self.on_files:
                self.on_files(filtered)
        except Exception as exc:
            log.error("Failed processing dropped files: %s", exc)
        finally:
            self._on_drag_leave(None)

    def _on_drag_enter(self, _event) -> None:
        self.configure(border_color=("dodgerblue", "dodgerblue"))

    def _on_drag_leave(self, _event) -> None:
        self.configure(border_color=("gray70", "gray30"))

    def _browse(self, filetypes) -> None:
        try:
            paths = filedialog.askopenfilenames(filetypes=filetypes)
            if paths and self.on_files:
                self.on_files(list(paths))
        except Exception as exc:
            log.error("File browse failed: %s", exc)
