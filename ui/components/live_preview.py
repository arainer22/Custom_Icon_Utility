"""
IconForge live icon preview widget.

Shows a preview of the new icon the user has selected, mimicking how it will
look on the desktop.
"""

from __future__ import annotations

import io
import logging
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageTk

log = logging.getLogger(__name__)


class LivePreview(ctk.CTkFrame):
    """Display a preview of the converted icon at near-desktop size."""

    PREVIEW_SIZE = (80, 80)

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(corner_radius=12, fg_color=("gray92", "gray17"))

        self._placeholder_photo = self._create_placeholder_photo()
        self._image_ref: ImageTk.PhotoImage = self._placeholder_photo

        self.icon_label = tk.Label(
            self,
            image=self._placeholder_photo,
            text="No icon selected",
            compound="center",
            width=100,
            height=100,
            bg=self._resolve_bg_color(),
            fg="#666666",
            bd=0,
            highlightthickness=0,
        )
        self.icon_label.pack(padx=12, pady=(12, 4))

        self.name_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            justify="center",
            wraplength=110,
        )
        self.name_label.pack(padx=8, pady=(0, 10))

    def _resolve_bg_color(self) -> str:
        fg_color = self.cget("fg_color")
        if isinstance(fg_color, tuple):
            return fg_color[1]
        return str(fg_color)

    def _create_placeholder_photo(self) -> ImageTk.PhotoImage:
        placeholder = Image.new("RGBA", self.PREVIEW_SIZE, (0, 0, 0, 0))
        return ImageTk.PhotoImage(placeholder)

    def update_preview(
        self,
        image_path: str | None = None,
        png_bytes: bytes | None = None,
        label: str = "",
    ) -> None:
        """Update the preview from either a file path or raw PNG bytes."""
        pil_image: Image.Image | None = None

        try:
            if image_path:
                with Image.open(image_path) as opened_image:
                    pil_image = opened_image.convert("RGBA")
            elif png_bytes:
                with Image.open(io.BytesIO(png_bytes)) as opened_image:
                    pil_image = opened_image.convert("RGBA")
        except Exception as exc:
            log.warning("LivePreview failed to load image: %s", exc)

        if pil_image is not None:
            pil_image.thumbnail(self.PREVIEW_SIZE, Image.LANCZOS)
            self._image_ref = ImageTk.PhotoImage(pil_image)
            self.icon_label.configure(image=self._image_ref, text="")
        else:
            self._image_ref = self._placeholder_photo
            self.icon_label.configure(image=self._placeholder_photo, text="No icon selected")

        self.name_label.configure(text=label)

    def clear(self) -> None:
        self._image_ref = self._placeholder_photo
        self.icon_label.configure(image=self._placeholder_photo, text="No icon selected")
        self.name_label.configure(text="")
