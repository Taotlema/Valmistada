# output_screen: Trial accordion list with per-file download buttons.

import os
import shutil

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                              QWidget, QFileDialog, QMessageBox)
from PyQt6.QtCore    import Qt

from ui.base.base_screen            import BaseScreen
from ui.base.base_widget            import THEME
from ui.components.button           import SecondaryButton
from ui.components.scroll_area      import AppScrollArea
from ui.components.dropdown         import DropdownRow, FileRow
from data.loaders.output_loader     import OutputLoader
from app_controller.event_bus       import EventBus, Events
from app_controller.screen_manager  import ScreenManager

_MONO = THEME["font"]


# OutputScreen: Lists completed trials and lets the user download individual monthly files.
class OutputScreen(BaseScreen):

    def __init__(self, bus: EventBus, settings: dict, app_controller):
        self._ctrl = app_controller
        super().__init__(bus, settings)
        self.bus.subscribe(Events.TRIAL_SAVED, lambda _: self.refresh())

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_topbar())
        self._scroll = AppScrollArea()
        root.addWidget(self._scroll, 1)
        root.addWidget(self._make_bottombar())
        self.refresh()

    def _make_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(38)
        bar.setStyleSheet(
            f"background-color: {THEME['surface']};"
            "border-bottom: 1px solid #555555;"
        )
        hbox = QHBoxLayout(bar)
        hbox.setContentsMargins(12, 0, 12, 0)
        hbox.setSpacing(12)

        back_btn = SecondaryButton("[ < BACK ]")
        back_btn.setFixedWidth(100)
        back_btn.setFixedHeight(26)
        back_btn.clicked.connect(
            lambda: self._ctrl.screen_manager.navigate(ScreenManager.START)
        )

        title = QLabel("// OUTPUT DATA")
        title.setStyleSheet(
            f"color: {THEME['primary']}; font-size: 11px; font-weight: bold;"
            f"font-family: {_MONO}; letter-spacing: 2px; background: transparent;"
        )

        refresh_btn = SecondaryButton("[ REFRESH ]")
        refresh_btn.setFixedWidth(110)
        refresh_btn.setFixedHeight(26)
        refresh_btn.clicked.connect(self.refresh)

        hbox.addWidget(back_btn)
        hbox.addWidget(title)
        hbox.addStretch()
        hbox.addWidget(refresh_btn)
        return bar

    def _make_bottombar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(36)
        bar.setStyleSheet(
            f"background-color: {THEME['surface']};"
            "border-top: 1px solid #555555;"
        )
        hbox = QHBoxLayout(bar)
        hbox.setContentsMargins(12, 0, 12, 0)
        self._footer_lbl = QLabel("NO TRIALS ON DISK")
        self._footer_lbl.setStyleSheet(
            f"color: {THEME['muted']}; font-size: 9px; font-family: {_MONO};"
            "letter-spacing: 1px; background: transparent;"
        )
        hbox.addWidget(self._footer_lbl)
        hbox.addStretch()
        return bar

    # refresh: Rescan the output folder and rebuild trial accordion rows.
    def refresh(self):
        self._scroll.clear()
        trials = OutputLoader(self._ctrl.output_root).scan_trials()

        if not trials:
            lbl = QLabel("  NO TRIALS FOUND - RUN A SIMULATION TO GENERATE OUTPUT")
            lbl.setStyleSheet(
                f"color: {THEME['muted']}; font-size: 10px; font-family: {_MONO};"
                "padding: 20px;"
            )
            self._scroll.add_widget(lbl)
            self._footer_lbl.setText("NO TRIALS ON DISK")
            return

        total_files = sum(len(m.files) for m in trials)
        self._footer_lbl.setText(
            f"{len(trials)} TRIAL(S) ON DISK  ·  {total_files} FILES TOTAL"
        )

        for meta in reversed(trials):
            row = DropdownRow(
                f"  TRIAL {meta.trial_number:03d}  ·  {len(meta.files)} FILES"
            )
            for fname in meta.files:
                file_row = FileRow(fname, action_label="DL")
                file_row.action_clicked.connect(
                    lambda fn, d=meta.trial_dir: self._download_file(d, fn)
                )
                row.add_item(file_row)
            self._scroll.add_widget(row)

    # _download_file: Copy a trial file to a user-chosen save location.
    def _download_file(self, trial_dir: str, filename: str):
        src     = os.path.join(trial_dir, filename)
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save file as", filename,
            "Text/CSV files (*.txt *.csv);;All files (*)",
        )
        if not dest:
            return
        try:
            shutil.copy2(src, dest)
            QMessageBox.information(self, "Saved", f"File saved:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file:\n{e}")
