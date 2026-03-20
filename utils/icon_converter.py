"""
IconForge image-to-ICO converter and preview extractor.

Uses Pillow with LANCZOS resampling for high-quality, high-DPI icons.
"""

from __future__ import annotations

import io
import logging
import os
import uuid

from PIL import Image, ImageOps, UnidentifiedImageError

from utils.constants import ICONS_DIR, ICO_SIZES

log = logging.getLogger(__name__)


def _render_icon_frame(source: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Fit the source into a square transparent canvas without distorting it."""
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    contained = ImageOps.contain(source, size, Image.LANCZOS)
    x_pos = (size[0] - contained.width) // 2
    y_pos = (size[1] - contained.height) // 2
    canvas.paste(contained, (x_pos, y_pos), contained)
    return canvas


def convert_to_ico(image_path: str, output_dir: str | None = None) -> str:
    """
    Convert a supported image to a multi-resolution .ico file.

    Returns the absolute path to the new .ico file.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    output_dir = output_dir or ICONS_DIR
    os.makedirs(output_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex[:12]}.ico"
    out_path = os.path.join(output_dir, unique_name)

    try:
        with Image.open(image_path) as opened_image:
            source = opened_image.convert("RGBA")
            icon_images = [_render_icon_frame(source, size) for size in ICO_SIZES]
            icon_images[-1].save(
                out_path,
                format="ICO",
                append_images=icon_images[:-1],
                sizes=ICO_SIZES,
            )
    except UnidentifiedImageError as exc:
        log.error("Unsupported image format for %s: %s", image_path, exc)
        raise ValueError(f"Unsupported image format: {image_path}") from exc
    except OSError as exc:
        log.error("Failed to convert %s to ICO: %s", image_path, exc)
        raise

    log.info("Converted %s -> %s", image_path, out_path)
    return out_path


def extract_preview_png(source: str, size: tuple[int, int] = (64, 64)) -> bytes:
    """
    Extract a PNG thumbnail from an image or .ico file.

    Returns raw PNG bytes suitable for display in a Tkinter/CTk widget.
    """
    if not source or not os.path.isfile(source):
        return b""

    try:
        with Image.open(source) as opened_image:
            img = opened_image.convert("RGBA")
            img.thumbnail(size, Image.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
    except (UnidentifiedImageError, OSError) as exc:
        log.warning("Could not extract preview from %s: %s", source, exc)
        return b""
