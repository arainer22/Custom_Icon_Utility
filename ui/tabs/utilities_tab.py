"""
IconForge "Utilities" tab.

Houses the theme switcher, desktop refresh, and restore flows.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import TYPE_CHECKING

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from utils.manifest_manager import delete_custom_icon, load_manifest, save_manifest
from utils.refresh import refresh_desktop
from utils.shortcut_handler import clear_icon_override, restore_original_name, set_icon_location

if TYPE_CHECKING:
    from ui.main_app import IconForgeApp

log = logging.getLogger(__name__)


def _safe_refresh() -> None:
    try:
        refresh_desktop()
    except Exception as exc:
        log.warning("Desktop refresh failed: %s", exc)


def _format_result_section(title: str, items: list[str], limit: int = 6) -> str:
    if not items:
        return ""
    shown = items[:limit]
    extra = len(items) - len(shown)
    suffix = f"\n...and {extra} more." if extra > 0 else ""
    return f"{title}:\n" + "\n".join(shown) + suffix


def _icon_source_available(icon_location: str | None) -> bool:
    if icon_location is None:
        return True
    icon_path = icon_location.rsplit(",", 1)[0].strip().strip('"')
    if not icon_path:
        return True
    return os.path.exists(icon_path)


class UtilitiesTab(ctk.CTkFrame):
    def __init__(self, master, app: IconForgeApp, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.restore_session_btn: ctk.CTkButton | None = None
        self.restore_all_btn: ctk.CTkButton | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        row = 0

        theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        theme_frame.grid(row=row, column=0, sticky="ew", padx=24, pady=(24, 8))

        ctk.CTkLabel(
            theme_frame, text="Theme:", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(0, 12))

        self.theme_var = ctk.StringVar(value=self.app.config.theme)
        ctk.CTkOptionMenu(
            theme_frame,
            values=["dark", "light", "system"],
            variable=self.theme_var,
            command=self._change_theme,
            width=140,
        ).pack(side="left")
        row += 1

        ctk.CTkButton(
            self,
            text="Refresh Desktop Icons",
            font=ctk.CTkFont(size=13),
            height=40,
            command=self._refresh,
        ).grid(row=row, column=0, sticky="ew", padx=80, pady=6)
        row += 1

        self.restore_session_btn = ctk.CTkButton(
            self,
            text="Restore Current Session",
            font=ctk.CTkFont(size=13),
            height=40,
            command=self._restore_current_session,
        )
        self.restore_session_btn.grid(row=row, column=0, sticky="ew", padx=80, pady=6)
        row += 1

        self.restore_all_btn = ctk.CTkButton(
            self,
            text="Restore All Tracked Shortcuts",
            font=ctk.CTkFont(size=13),
            height=40,
            command=self._restore_all_tracked,
        )
        self.restore_all_btn.grid(row=row, column=0, sticky="ew", padx=80, pady=6)
        row += 1

        self.grid_rowconfigure(row, weight=1)
        self.refresh_restore_buttons()

    def refresh_restore_buttons(self) -> None:
        if self.restore_session_btn is not None:
            has_session_items = bool(self.app.session_modified_shortcuts)
            self.restore_session_btn.configure(
                state="normal" if has_session_items else "disabled"
            )

    def _change_theme(self, value: str) -> None:
        try:
            ctk.set_appearance_mode(value)
            self.app.config.theme = value
            self.app.config.save()
            log.info("Theme changed to %s", value)
        except Exception as exc:
            log.error("Failed to change theme to %s: %s", value, exc)
            CTkMessagebox(
                title="Theme Error",
                message=f"Could not save the selected theme:\n{exc}",
                icon="cancel",
            )

    def _refresh(self) -> None:
        threading.Thread(target=_safe_refresh, daemon=True).start()
        CTkMessagebox(title="Done", message="Desktop icons refreshed.", icon="check")

    def _restore_current_session(self) -> None:
        self._restore_entries(
            mode="session",
            confirmation=(
                "Restore only shortcuts modified since this app launch?\n\n"
                "Missing shortcuts will be skipped and preserved in IconForge history."
            ),
        )

    def _restore_all_tracked(self) -> None:
        self._restore_entries(
            mode="all",
            confirmation=(
                "Restore all shortcuts recorded in IconForge history, including "
                "previous sessions?\n\nMissing shortcuts will be skipped and preserved "
                "in IconForge history."
            ),
        )

    def _restore_entries(self, mode: str, confirmation: str) -> None:
        manifest = load_manifest()
        if not manifest:
            CTkMessagebox(
                title="Nothing to Restore",
                message="No modified shortcuts are recorded in the manifest.",
                icon="info",
            )
            return

        if mode == "session":
            manifest = {
                path: entry
                for path, entry in manifest.items()
                if path in self.app.session_modified_shortcuts
            }
            if not manifest:
                CTkMessagebox(
                    title="Nothing to Restore",
                    message="No shortcuts from the current session are recorded.",
                    icon="info",
                )
                return

        confirm = CTkMessagebox(
            title="Confirm Restore",
            message=confirmation,
            icon="question",
            option_1="Cancel",
            option_2="Restore",
        )
        if confirm.get() != "Restore":
            return

        restored: list[str] = []
        skipped_missing: list[str] = []
        partial_icon_missing: list[str] = []
        errors: list[str] = []

        full_manifest = load_manifest()
        remaining_manifest = dict(full_manifest)

        for original_lnk_path, entry in manifest.items():
            current_path = entry.get("current_path", original_lnk_path)
            working_path = current_path
            original_name = entry.get("original_name")
            original_icon_location = entry.get("original_icon_location")
            custom_icon = entry.get("custom_icon")
            display_name = original_name or os.path.basename(current_path) or original_lnk_path

            if not os.path.isfile(working_path) and os.path.isfile(original_lnk_path):
                working_path = original_lnk_path

            if not os.path.isfile(working_path):
                entry["current_path"] = current_path
                remaining_manifest[original_lnk_path] = entry
                skipped_missing.append(display_name)
                log.warning("Skipping restore for missing shortcut: %s", current_path)
                continue

            try:
                if original_name and os.path.basename(working_path) != original_name:
                    working_path = restore_original_name(working_path, original_name)

                if original_icon_location is not None:
                    if _icon_source_available(original_icon_location):
                        set_icon_location(working_path, original_icon_location)
                        delete_custom_icon(custom_icon)
                        remaining_manifest.pop(original_lnk_path, None)
                        restored.append(display_name)
                        self.app.session_modified_shortcuts.discard(original_lnk_path)
                    else:
                        entry["current_path"] = working_path
                        remaining_manifest[original_lnk_path] = entry
                        partial_icon_missing.append(display_name)
                        log.warning(
                            "Original icon source is missing for shortcut %s",
                            working_path,
                        )
                else:
                    clear_icon_override(working_path)
                    delete_custom_icon(custom_icon)
                    remaining_manifest.pop(original_lnk_path, None)
                    restored.append(display_name)
                    self.app.session_modified_shortcuts.discard(original_lnk_path)
            except Exception as exc:
                entry["current_path"] = working_path
                remaining_manifest[original_lnk_path] = entry
                errors.append(f"{display_name}: {exc}")
                log.error("Failed restoring shortcut %s: %s", current_path, exc)

        try:
            save_manifest(remaining_manifest)
        except Exception as exc:
            errors.append(f"Manifest save failed: {exc}")

        self.refresh_restore_buttons()
        threading.Thread(target=_safe_refresh, daemon=True).start()

        parts = [
            _format_result_section("Restored successfully", restored),
            _format_result_section(
                "Skipped because the shortcut is missing", skipped_missing
            ),
            _format_result_section(
                "Partially restored because the original icon source is unavailable",
                partial_icon_missing,
            ),
            _format_result_section("Failed to restore", errors),
        ]
        parts = [part for part in parts if part]

        if len(parts) == 1 and restored and not skipped_missing and not partial_icon_missing and not errors:
            CTkMessagebox(
                title="Restored",
                message=parts[0],
                icon="check",
            )
        else:
            CTkMessagebox(
                title="Restore Results",
                message="\n\n".join(parts),
                icon="warning" if (skipped_missing or partial_icon_missing or errors) else "check",
            )
