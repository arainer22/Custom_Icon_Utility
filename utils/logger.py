"""
IconForge logging configuration.

Logs are written to %AppData%/IconForge/app.log and rotated at 2 MB.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from utils.constants import APP_DATA_DIR, LOG_PATH


def setup_logging() -> None:
    """Initialise the root logger with file + console handlers exactly once."""
    os.makedirs(APP_DATA_DIR, exist_ok=True)

    root = logging.getLogger()
    if getattr(root, "_iconforge_logging_configured", False):
        return

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = RotatingFileHandler(
        LOG_PATH, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    root.setLevel(logging.DEBUG)
    root.addHandler(fh)
    root.addHandler(ch)
    root._iconforge_logging_configured = True
