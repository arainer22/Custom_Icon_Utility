"""
IconForge data models used across the application.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ShortcutInfo:
    """Represent a single .lnk shortcut and its metadata."""

    lnk_path: str
    target: str = ""
    icon_location: str | None = None
    current_icon: str | None = None
    icon_preview_bytes: bytes | None = None
    original_name: str | None = None


BatchJob = list[ShortcutInfo]
