"""
IconForge entry point.

Initialises logging, loads config, creates the TkinterDnD root window, and
hands off to the main application controller.
"""

from __future__ import annotations

import logging
import os
import sys
from tkinter import messagebox

if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.abspath(__file__))

if _base not in sys.path:
    sys.path.insert(0, _base)

from utils.config_manager import AppConfig
from utils.constants import APP_DATA_DIR, ICONS_DIR
from utils.logger import setup_logging

log = logging.getLogger(__name__)


def main() -> None:
    setup_logging()

    try:
        os.makedirs(APP_DATA_DIR, exist_ok=True)
        os.makedirs(ICONS_DIR, exist_ok=True)

        config = AppConfig.load()

        import customtkinter as ctk
        import tkinterdnd2

        ctk.set_appearance_mode(config.theme)
        ctk.set_default_color_theme("blue")

        root = tkinterdnd2.TkinterDnD.Tk()

        from ui.main_app import IconForgeApp

        app = IconForgeApp(root, config=config)
        app.mainloop()
    except Exception as exc:
        log.exception("Fatal application startup error")
        try:
            messagebox.showerror(
                "IconForge Startup Error",
                f"IconForge could not start successfully.\n\n{exc}",
            )
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
