"""
Filename: input_screen.py
Author: Ayemhenre Isikhuemhen
Description: Input screen — city accordion bars with GTFS file listings and upload button.
Last Updated: March, 2026
"""

# Libraries
import os
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                              QWidget, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Modules
from ui.base.base_screen import BaseScreen
from ui.base.base_widget import THEME
from ui.components.button import PrimaryButton, SecondaryButton
from ui.components.scroll_area import AppScrollArea
from ui.components.dropdown import DropdownRow, FileRow
from app_controller.event_bus import EventBus, Events
from app_controller.screen_manager import ScreenManager


# InputScreen: Browse and manage GTFS city data sources
class InputScreen(BaseScreen):

    # __init__ (bus, settings, app_controller)
    def __init__(self, bus: EventBus, settings: dict, app_controller):
        self._ctrl = app_controller
        self._city_rows: dict = {}
        super().__init__(bus, settings)
        self.bus.subscribe(Events.GTFS_LOADED, self._on_gtfs_loaded)

    # _build: Header, scrollable city list, bottom toolbar
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_topbar())

        self._scroll = AppScrollArea()
        root.addWidget(self._scroll, 1)

        root.addWidget(self._make_bottombar())
        self._seed_default_city()

    # _make_topbar: Screen title + back button
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

        title = QLabel("Input Data")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {THEME['text']}; background: transparent;")

        hbox.addWidget(back_btn)
        hbox.addSpacing(16)
        hbox.addWidget(title)
        hbox.addStretch()
        return bar

    # _make_bottombar: Upload button
    def _make_bottombar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(58)
        bar.setStyleSheet(
            f"background-color: {THEME['surface']}; border-top: 1px solid {THEME['border']};"
        )
        hbox = QHBoxLayout(bar)
        hbox.setContentsMargins(24, 0, 24, 0)
        hbox.addStretch()

        upload_btn = PrimaryButton("+ Upload GTFS Folder")
        upload_btn.setFixedWidth(200)
        upload_btn.clicked.connect(self._upload_gtfs)
        hbox.addWidget(upload_btn)
        return bar

    # _seed_default_city: Populate the default San Francisco entry
    def _seed_default_city(self):
        sf_dir = os.path.join(
            self._ctrl.gtfs_root, "San Francisco (muni_gtfs-current)"
        )
        if os.path.isdir(sf_dir):
            self._add_city_row("San Francisco", sf_dir)

    # _add_city_row (city_label, gtfs_dir): Build and register a DropdownRow
    def _add_city_row(self, city_label: str, gtfs_dir: str):
        if city_label in self._city_rows:
            return
        row = DropdownRow(f"🏙  {city_label}")
        self._populate_row(row, gtfs_dir)
        self._scroll.add_widget(row)
        self._city_rows[city_label] = (gtfs_dir, row)
        if city_label not in self._ctrl.feeds:
            self._ctrl.load_city_feed(city_label, gtfs_dir)

    # _populate_row (row, gtfs_dir): Add one FileRow per .txt file found
    def _populate_row(self, row: DropdownRow, gtfs_dir: str):
        row.clear_items()
        if not os.path.isdir(gtfs_dir):
            row.add_item(QLabel("  ⚠  Directory not found"))
            return
        txt_files = sorted(f for f in os.listdir(gtfs_dir) if f.endswith(".txt"))
        if not txt_files:
            info = QLabel("  No .txt files found")
            info.setStyleSheet(f"color: {THEME['muted']}; font-size: 12px;")
            row.add_item(info)
            return
        for fname in txt_files:
            row.add_item(FileRow(fname))

    # _on_gtfs_loaded (city_label): Update header with route count
    def _on_gtfs_loaded(self, city_label: str):
        if city_label in self._city_rows:
            gtfs_dir, row = self._city_rows[city_label]
            feed = self._ctrl.feeds.get(city_label)
            n    = len(feed.routes) if feed else 0
            row.set_title(f"🏙  {city_label}  ·  {n} routes loaded")

    # _upload_gtfs: Open folder picker and register new city
    def _upload_gtfs(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select GTFS folder", "",
            QFileDialog.Option.ShowDirsOnly
        )
        if not folder:
            return
        city_label = os.path.basename(folder)
        self._add_city_row(city_label, folder)