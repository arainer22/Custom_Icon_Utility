"""
IconForge persistent user configuration (JSON-backed).

Config lives at %AppData%/IconForge/config.json.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass

from utils.constants import APP_DATA_DIR, CONFIG_PATH

log = logging.getLogger(__name__)


def _write_json_atomic(path: str, payload: dict[str, object]) -> None:
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    os.replace(temp_path, path)


@dataclass
class AppConfig:
    """User-facing settings that persist between sessions."""

    theme: str = "dark"

    def save(self) -> None:
        os.makedirs(APP_DATA_DIR, exist_ok=True)
        try:
            _write_json_atomic(CONFIG_PATH, asdict(self))
            log.debug("Config saved to %s", CONFIG_PATH)
        except OSError as exc:
            log.error("Failed to save config to %s: %s", CONFIG_PATH, exc)
            raise

    @classmethod
    def load(cls) -> AppConfig:
        if not os.path.isfile(CONFIG_PATH):
            return cls()

        try:
            with open(CONFIG_PATH, encoding="utf-8") as handle:
                data = json.load(handle)

            if not isinstance(data, dict):
                raise TypeError("config root must be a JSON object")

            filtered = {
                key: value
                for key, value in data.items()
                if key in cls.__dataclass_fields__
            }
            config = cls(**filtered)
            if config.theme not in {"dark", "light", "system"}:
                log.warning("Invalid theme value %r in config; using default", config.theme)
                config.theme = cls().theme
            log.debug("Config loaded from %s", CONFIG_PATH)
            return config
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
            log.warning("Corrupt config detected at %s; using defaults: %s", CONFIG_PATH, exc)
            return cls()
