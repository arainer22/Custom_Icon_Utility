"""
IconForge manifest manager for tracking original shortcut names and icons.

The manifest lives at %AppData%/IconForge/manifest.json and records the
original display name and icon of each shortcut that IconForge has modified,
so that "Restore All" can undo every change.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from utils.constants import APP_DATA_DIR, MANIFEST_PATH

log = logging.getLogger(__name__)

ManifestEntry = dict[str, Any]
ManifestData = dict[str, ManifestEntry]


def _write_json_atomic(path: str, payload: ManifestData) -> None:
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    os.replace(temp_path, path)


def load_manifest() -> ManifestData:
    """Load the manifest from disk and return an empty dict on error."""
    if not os.path.isfile(MANIFEST_PATH):
        return {}

    try:
        with open(MANIFEST_PATH, encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise TypeError("manifest root must be a JSON object")
        return data
    except (json.JSONDecodeError, OSError, TypeError) as exc:
        log.warning("Failed to load manifest from %s: %s", MANIFEST_PATH, exc)
        return {}


def save_manifest(data: ManifestData) -> None:
    """Persist the manifest atomically."""
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    try:
        _write_json_atomic(MANIFEST_PATH, data)
    except OSError as exc:
        log.error("Failed to save manifest to %s: %s", MANIFEST_PATH, exc)
        raise


def record_original(
    lnk_path: str,
    original_name: str | None = None,
    original_icon: str | None = None,
    original_icon_location: str | None = None,
    custom_icon: str | None = None,
) -> None:
    """
    Record or update the original state of a shortcut so it can be restored.

    Only the first recorded original name/icon wins, which prevents already
    modified state from being captured as the baseline.
    """
    manifest = load_manifest()
    entry = manifest.setdefault(lnk_path, {})

    if original_name and "original_name" not in entry:
        entry["original_name"] = original_name
    if original_icon is not None and "original_icon" not in entry:
        entry["original_icon"] = original_icon
    if original_icon_location is not None and "original_icon_location" not in entry:
        entry["original_icon_location"] = original_icon_location
    if custom_icon:
        entry["custom_icon"] = custom_icon
    entry["current_path"] = entry.get("current_path", lnk_path)

    manifest[lnk_path] = entry
    save_manifest(manifest)
    log.debug("Manifest updated for %s", lnk_path)


def update_current_path(original_lnk_path: str, current_lnk_path: str) -> None:
    """Track the live path for a shortcut that was renamed after modification."""
    manifest = load_manifest()
    entry = manifest.get(original_lnk_path)
    if not entry:
        log.debug(
            "Manifest entry missing when updating current path: %s -> %s",
            original_lnk_path,
            current_lnk_path,
        )
        return

    entry["current_path"] = current_lnk_path
    manifest[original_lnk_path] = entry
    save_manifest(manifest)
    log.debug("Manifest current path updated: %s -> %s", original_lnk_path, current_lnk_path)


def delete_custom_icon(icon_path: str | None) -> None:
    """Delete a generated custom icon on a best-effort basis."""
    if not icon_path or not os.path.isfile(icon_path):
        return

    try:
        os.remove(icon_path)
        log.debug("Deleted custom icon %s", icon_path)
    except OSError as exc:
        log.warning("Could not delete %s: %s", icon_path, exc)
