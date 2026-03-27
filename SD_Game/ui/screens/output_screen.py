"""
Filename: output_screen.py
Author: Ayemhenre Isikhuemhen
Description: Output screen — accordion list of trial folders, each expandable
             to show monthly .txt files with individual download buttons.
Last Updated: March, 2026
"""

# Libraries
import os
import shutil
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                              QWidget, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Modules
from ui.base.base_screen import BaseScreen
from ui.base.base_widget import THEME
from ui.components.button import SecondaryButton
from ui.components.scroll_area import AppScrollArea
from ui.components.dropdown import DropdownRow, FileRow
from data.loaders.output_loader import OutputLoader
from app_controller.event_bus import EventBus, Events
from app_controller.screen_manager import ScreenManager


# OutputScreen: Browse and download synthetic ridership trial files
class OutputScreen(BaseScreen):

    # __init__ (bus, settings, app_controller)
    def __init__(self, bus: EventBus, settings: dict, app_controller):
        self._ctrl = app_controller
        super().__init__(bus, settings)
        self.bus.subscribe(Events.TRIAL_SAVED, lambda _: self.refresh())

    # _build: Header, scrollable trial list
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_topbar())
        self._scroll = AppScrollArea()
        root.addWidget(self._scroll, 1)
        self.refresh()

    # _make_topbar: Title + back + refresh buttons
    def _make_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(60)
        bar.setStyleSheet(
            f"background-color: {THEME['surface']}; border-bottom: 1px solid {THEME['border']};"
        )
        hbox = QHBoxLayout(bar)
        hbox.setContentsMargins(24, 0, 24, 0)

        back_btn = SecondaryButton("← Back")
        back_btn.setFixedWidth(90)
        back_btn.clicked.connect(
            lambda: self._ctrl.screen_manager.navigate(ScreenManager.START))

        title = QLabel("Output Data")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {THEME['text']}; background: transparent;")

        refresh_btn = SecondaryButton("↺  Refresh")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.refresh)

        hbox.addWidget(back_btn)
        hbox.addSpacing(16)
        hbox.addWidget(title)
        hbox.addStretch()
        hbox.addWidget(refresh_btn)
        return bar

    # refresh: Rescan output folder and rebuild trial rows
    def refresh(self):
        self._scroll.clear()
        loader = OutputLoader(self._ctrl.output_root)
        trials = loader.scan_trials()

        if not trials:
            empty_lbl = QLabel("  No trials found. Run a simulation to generate output.")
            empty_lbl.setStyleSheet(
                f"color: {THEME['muted']}; font-size: 13px; padding: 20px;"
            )
            self._scroll.add_widget(empty_lbl)
            return

        for meta in reversed(trials):
            row = DropdownRow(f"📁  Trial {meta.trial_number}  ·  {len(meta.files)} files")
            for fname in meta.files:
                file_row = FileRow(fname, action_label="Download")
                file_row.action_clicked.connect(
                    lambda fn, d=meta.trial_dir: self._download_file(d, fn)
                )
                row.add_item(file_row)
            self._scroll.add_widget(row)

    # _download_file (trial_dir, filename): Copy file to a user-chosen location
    def _download_file(self, trial_dir: str, filename: str):
        src = os.path.join(trial_dir, filename)
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save file as", filename,
            "Text/CSV files (*.txt *.csv);;All files (*)"
        )
        if not dest:
            return
        try:
            shutil.copy2(src, dest)
            QMessageBox.information(self, "Saved", f"File saved to:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file:\n{e}")