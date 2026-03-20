"""
IconForge scrollable list showing the shortcuts queued for modification.
"""

from __future__ import annotations

import io
import logging
import os

import customtkinter as ctk
from PIL import Image

from utils.models import ShortcutInfo

log = logging.getLogger(__name__)


class BatchListFrame(ctk.CTkScrollableFrame):
    """Display a scrollable list of shortcut entries with thumbnails."""

    THUMB_SIZE = (36, 36)

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._rows: list[ctk.CTkFrame] = []
        self._images: list[ctk.CTkImage] = []

    def populate(self, shortcuts: list[ShortcutInfo]) -> None:
        """Clear the list and rebuild it from *shortcuts*."""
        self.clear()
        for info in shortcuts:
            self._add_row(info)

    def clear(self) -> None:
        for row in self._rows:
            row.destroy()
        self._rows.clear()
        self._images.clear()

    def _add_row(self, info: ShortcutInfo) -> None:
        row = ctk.CTkFrame(self, corner_radius=8)
        row.pack(fill="x", padx=4, pady=3)

        thumb_img = self._bytes_to_ctkimage(info.icon_preview_bytes)
        if thumb_img:
            self._images.append(thumb_img)
            ctk.CTkLabel(row, image=thumb_img, text="").pack(
                side="left", padx=(8, 6), pady=6
            )

        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=6)

        labels = []

        name = info.original_name or os.path.basename(info.lnk_path) or info.lnk_path
        name_label = ctk.CTkLabel(
            text_frame,
            text=name,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            justify="left",
        )
        name_label.pack(fill="x")
        labels.append(name_label)

        if info.target:
            target_label = ctk.CTkLabel(
                text_frame,
                text=f"Target: {info.target}",
                font=ctk.CTkFont(size=11),
                text_color=("gray45", "gray65"),
                anchor="w",
                justify="left",
            )
            target_label.pack(fill="x", pady=(1, 0))
            labels.append(target_label)

        icon_source = info.icon_location or info.current_icon or "Default shortcut icon"
        icon_label = ctk.CTkLabel(
            text_frame,
            text=f"Current icon: {icon_source}",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray65"),
            anchor="w",
            justify="left",
        )
        icon_label.pack(fill="x", pady=(1, 0))
        labels.append(icon_label)

        self._configure_wraplabels(text_frame, labels)
        self._rows.append(row)

    def _configure_wraplabels(
        self, container: ctk.CTkFrame, labels: list[ctk.CTkLabel]
    ) -> None:
        """Update wrap lengths conservatively so labels remain readable."""

        def update_wrap(_event=None) -> None:
            available_width = max(container.winfo_width() - 12, 220)
            for label in labels:
                previous = getattr(label, "_iconforge_wraplength", None)
                if previous is None or abs(previous - available_width) > 24:
                    label.configure(wraplength=available_width)
                    label._iconforge_wraplength = available_width

        container.bind("<Configure>", update_wrap, add="+")
        container.after_idle(update_wrap)

    @classmethod
    def _bytes_to_ctkimage(cls, data: bytes | None) -> ctk.CTkImage | None:
        if not data:
            return None

        try:
            with Image.open(io.BytesIO(data)) as opened_image:
                pil_img = opened_image.convert("RGBA")
            return ctk.CTkImage(
                light_image=pil_img,
                dark_image=pil_img,
                size=cls.THUMB_SIZE,
            )
        except Exception as exc:
            log.debug("Could not create thumbnail: %s", exc)
            return None
