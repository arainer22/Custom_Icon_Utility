"""
IconForge "Change Icon" tab.

Flow:
1. User drops or browses .lnk files and a batch is built.
2. User drops or browses a new image and it is converted to .ico.
3. User clicks Apply and icons and/or labels are changed on each shortcut.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import TYPE_CHECKING

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from ui.components.batch_list_frame import BatchListFrame
from ui.components.drop_zone import DropZone
from ui.components.live_preview import LivePreview
from utils.icon_converter import convert_to_ico, extract_preview_png
from utils.manifest_manager import record_original, update_current_path
from utils.models import BatchJob
from utils.refresh import refresh_desktop
from utils.shortcut_handler import read_shortcut, rename_lnk_for_invisible_label, update_icon

if TYPE_CHECKING:
    from ui.main_app import IconForgeApp

log = logging.getLogger(__name__)


def _safe_refresh() -> None:
    try:
        refresh_desktop()
    except Exception as exc:
        log.warning("Desktop refresh failed: %s", exc)


class ChangeIconTab(ctk.CTkFrame):
    def __init__(self, master, app: IconForgeApp, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.batch: BatchJob = []
        self.new_ico_path: str | None = None
        self._batch_paths: set[str] = set()
        self._selected_image_name = ctk.StringVar(value="No replacement image selected")

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        row = 0

        step1_label = ctk.CTkLabel(
            self,
            text="Step 1: Add shortcuts",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        step1_label.grid(row=row, column=0, sticky="ew", padx=16, pady=(12, 2))
        row += 1

        self.shortcut_drop = DropZone(
            self, accept="lnk", on_files=self._on_shortcuts_added, height=96
        )
        self.shortcut_drop.grid(row=row, column=0, sticky="ew", padx=16, pady=4)
        row += 1

        batch_row = row
        self.batch_list = BatchListFrame(self, height=220)
        self.batch_list.grid(row=row, column=0, sticky="nsew", padx=16, pady=4)
        self.grid_rowconfigure(batch_row, weight=3, minsize=140)
        row += 1

        step2_label = ctk.CTkLabel(
            self,
            text="Step 2: Choose new icon image",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        step2_label.grid(row=row, column=0, sticky="ew", padx=16, pady=(10, 2))
        row += 1

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(2, 4))
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.image_drop = DropZone(
            bottom_frame, accept="image", on_files=self._on_image_selected, height=84
        )
        self.image_drop.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.preview = LivePreview(bottom_frame, width=118)
        self.preview.grid(row=0, column=1, sticky="ns")
        row += 1

        self.selected_image_label = ctk.CTkLabel(
            self,
            textvariable=self._selected_image_name,
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray65"),
            anchor="w",
            justify="left",
        )
        self.selected_image_label.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 2))
        row += 1

        self.clear_image_btn = ctk.CTkButton(
            self,
            text="Clear Selected Image",
            width=170,
            height=30,
            command=self._clear_selected_image,
            state="disabled",
        )
        self.clear_image_btn.grid(row=row, column=0, sticky="w", padx=16, pady=(0, 6))
        row += 1

        opts_frame = ctk.CTkFrame(self, fg_color="transparent")
        opts_frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(4, 4))

        self.apply_icon_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opts_frame,
            text="Apply new icon",
            variable=self.apply_icon_var,
            command=self._update_apply_state,
        ).pack(side="left", padx=(0, 16))

        self.hide_label_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            opts_frame,
            text="Also hide the text label under the icon(s)",
            variable=self.hide_label_var,
            command=self._update_apply_state,
        ).pack(side="left")
        row += 1

        self.apply_btn = ctk.CTkButton(
            self,
            text="Apply Changes",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._apply,
            state="disabled",
        )
        self.apply_btn.grid(row=row, column=0, sticky="ew", padx=16, pady=(4, 16))

    def _on_shortcuts_added(self, paths: list[str]) -> None:
        added_count = 0
        for path in paths:
            normalized = os.path.normcase(os.path.abspath(path))
            if normalized in self._batch_paths:
                continue

            info = read_shortcut(path)
            source = info.current_icon or info.target
            if source and os.path.isfile(source):
                info.icon_preview_bytes = extract_preview_png(source)
            self.batch.append(info)
            self._batch_paths.add(normalized)
            added_count += 1

        self.batch_list.populate(self.batch)
        self._update_apply_state()
        log.info("Added %d shortcut(s); batch size now %d", added_count, len(self.batch))

    def _on_image_selected(self, paths: list[str]) -> None:
        if not paths:
            return

        image_path = paths[0]
        try:
            self.new_ico_path = convert_to_ico(image_path)
            preview_bytes = extract_preview_png(image_path, size=(80, 80))
            self.preview.update_preview(png_bytes=preview_bytes, label=os.path.basename(image_path))
            self._selected_image_name.set(f"Replacement image: {os.path.basename(image_path)}")
            self.clear_image_btn.configure(state="normal")
            self._update_apply_state()
        except Exception as exc:
            log.error("Image conversion failed for %s: %s", image_path, exc)
            CTkMessagebox(
                title="Conversion Error",
                message=f"Could not convert the selected image:\n{exc}",
                icon="cancel",
            )

    def _clear_selected_image(self) -> None:
        self.new_ico_path = None
        self._selected_image_name.set("No replacement image selected")
        self.preview.clear()
        self.clear_image_btn.configure(state="disabled")
        self._update_apply_state()

    def _update_apply_state(self) -> None:
        wants_icon = self.apply_icon_var.get() and bool(self.new_ico_path)
        wants_hidden_label = self.hide_label_var.get()
        has_work = bool(self.batch) and (wants_icon or wants_hidden_label)
        self.apply_btn.configure(state="normal" if has_work else "disabled")

    def _reset_state(self) -> None:
        self.batch.clear()
        self._batch_paths.clear()
        self.batch_list.clear()
        self.new_ico_path = None
        self._selected_image_name.set("No replacement image selected")
        self.preview.clear()
        self.clear_image_btn.configure(state="disabled")
        self.apply_btn.configure(state="disabled")

    def _apply(self) -> None:
        errors: list[str] = []

        for index, info in enumerate(self.batch):
            original_manifest_path = info.lnk_path
            shortcut_changed = False

            if self.apply_icon_var.get() and self.new_ico_path:
                try:
                    record_original(
                        info.lnk_path,
                        original_name=info.original_name,
                        original_icon=info.current_icon,
                        original_icon_location=info.icon_location,
                        custom_icon=self.new_ico_path,
                    )
                    update_icon(info.lnk_path, self.new_ico_path)
                    shortcut_changed = True
                except PermissionError:
                    errors.append(f"Permission denied: {info.original_name}")
                except Exception as exc:
                    errors.append(f"{info.original_name}: {exc}")

            if self.hide_label_var.get():
                try:
                    record_original(info.lnk_path, original_name=info.original_name)
                    new_path = rename_lnk_for_invisible_label(info.lnk_path, index)
                    info.lnk_path = new_path
                    update_current_path(original_manifest_path, new_path)
                    shortcut_changed = True
                except PermissionError:
                    errors.append(f"Permission denied renaming: {info.original_name}")
                except Exception as exc:
                    errors.append(f"Rename {info.original_name}: {exc}")

            if shortcut_changed:
                self.app.session_modified_shortcuts.add(original_manifest_path)

        threading.Thread(target=_safe_refresh, daemon=True).start()

        if errors:
            message = "Some shortcuts could not be modified:\n\n" + "\n".join(errors[:8])
            if len(errors) > 8:
                message += f"\n...and {len(errors) - 8} more."
            CTkMessagebox(
                title="Partial Success",
                message=message,
                icon="warning",
            )
        else:
            CTkMessagebox(title="Success", message="All changes applied.", icon="check")

        self.app.utilities_tab.refresh_restore_buttons()
        self._reset_state()
