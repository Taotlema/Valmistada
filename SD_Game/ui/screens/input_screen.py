# input_screen: Accordion city rows listing GTFS file contents.

import os

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                              QWidget, QFileDialog, QFrame)
from PyQt6.QtCore    import Qt

from ui.base.base_screen            import BaseScreen
from ui.base.base_widget            import THEME
from ui.components.button           import PrimaryButton, SecondaryButton
from ui.components.scroll_area      import AppScrollArea
from ui.components.dropdown         import DropdownRow, FileRow
from app_controller.event_bus       import EventBus, Events
from app_controller.screen_manager  import ScreenManager

_MONO = THEME["font"]


# InputScreen: Lets the user view loaded GTFS cities and add new ones from disk.
class InputScreen(BaseScreen):

    def __init__(self, bus: EventBus, settings: dict, app_controller):
        self._ctrl      = app_controller
        self._city_rows: dict = {}
        super().__init__(bus, settings)
        self.bus.subscribe(Events.GTFS_LOADED, self._on_gtfs_loaded)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_topbar())
        self._scroll = AppScrollArea()
        root.addWidget(self._scroll, 1)
        root.addWidget(self._make_bottombar())
        self._seed_default_city()

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

        title = QLabel("// INPUT DATA")
        title.setStyleSheet(
            f"color: {THEME['primary']}; font-size: 11px; font-weight: bold;"
            f"font-family: {_MONO}; letter-spacing: 2px; background: transparent;"
        )

        hbox.addWidget(back_btn)
        hbox.addWidget(title)
        hbox.addStretch()
        return bar

    def _make_bottombar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet(
            f"background-color: {THEME['surface']};"
            "border-top: 1px solid #555555;"
        )
        hbox = QHBoxLayout(bar)
        hbox.setContentsMargins(12, 0, 12, 0)

        info = QLabel("DRAG A GTFS FOLDER OR USE THE BUTTON TO ADD A CITY")
        info.setStyleSheet(
            f"color: {THEME['muted']}; font-size: 9px; font-family: {_MONO};"
            "letter-spacing: 1px; background: transparent;"
        )

        upload_btn = PrimaryButton("[ + UPLOAD GTFS FOLDER ]")
        upload_btn.setFixedWidth(220)
        upload_btn.setFixedHeight(28)
        upload_btn.clicked.connect(self._upload_gtfs)

        hbox.addWidget(info)
        hbox.addStretch()
        hbox.addWidget(upload_btn)
        return bar

    # _seed_default_city: Add the bundled San Francisco GTFS folder on first build.
    def _seed_default_city(self):
        sf_dir = os.path.join(
            self._ctrl.gtfs_root, "San Francisco (muni_gtfs-current)"
        )
        if os.path.isdir(sf_dir):
            self._add_city_row("San Francisco", sf_dir)

    # _add_city_row: Build and register a DropdownRow for one city folder.
    def _add_city_row(self, city_label: str, gtfs_dir: str):
        if city_label in self._city_rows:
            return
        row = DropdownRow(f"  {city_label}")
        self._populate_row(row, gtfs_dir)
        self._scroll.add_widget(row)
        self._city_rows[city_label] = (gtfs_dir, row)
        if city_label not in self._ctrl.feeds:
            self._ctrl.load_city_feed(city_label, gtfs_dir)

    # _populate_row: List every txt file in the GTFS directory with required-file markers.
    def _populate_row(self, row: DropdownRow, gtfs_dir: str):
        row.clear_items()
        if not os.path.isdir(gtfs_dir):
            row.add_item(QLabel("  ! DIRECTORY NOT FOUND"))
            return
        txt_files = sorted(f for f in os.listdir(gtfs_dir) if f.endswith(".txt"))
        if not txt_files:
            lbl = QLabel("  NO .TXT FILES FOUND")
            lbl.setStyleSheet(
                f"color: {THEME['muted']}; font-size: 10px; font-family: {_MONO};"
            )
            row.add_item(lbl)
            return
        # Mark the four required GTFS files with an asterisk
        required = {"routes.txt", "stops.txt", "trips.txt", "stop_times.txt"}
        for fname in txt_files:
            marker = "*" if fname in required else " "
            row.add_item(FileRow(f"{marker} {fname}"))

    # _on_gtfs_loaded: Update the row header with route count once loading completes.
    def _on_gtfs_loaded(self, city_label: str):
        if city_label in self._city_rows:
            _, row = self._city_rows[city_label]
            feed = self._ctrl.feeds.get(city_label)
            n    = len(feed.routes) if feed else 0
            row.set_title(f"  {city_label}  ·  {n} ROUTES LOADED")

    # _upload_gtfs: Open a folder picker and register the selected GTFS directory.
    def _upload_gtfs(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select GTFS folder", "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self._add_city_row(os.path.basename(folder), folder)
