# dictionary_screen: Scrollable glossary with subtle dark separators between entries.

import os

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QWidget)
from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QPixmap

from ui.base.base_screen            import BaseScreen
from ui.base.base_widget            import THEME
from ui.components.button           import SecondaryButton
from ui.components.scroll_area      import AppScrollArea
from app_controller.event_bus       import EventBus
from app_controller.screen_manager  import ScreenManager

_MONO = THEME["font"]

# All terms and definitions shown in the glossary
_GLOSSARY = [
    ("  GTFS",
     "  General Transit Feed Specification - the open standard for publishing public "
     "transit schedules and geographic data. This simulator reads GTFS txt files "
     "  to model the real SF MUNI network topology."),
    ("  ROUTE",
     "  A named transit service line (e.g. 1 California) running between two termini "
     "with a fixed stop sequence. Types: 0=Tram, 1=Subway, 3=Bus, 5=Cable Car."),
    ("  TRIP",
     "  A single scheduled run of a route on a service day. One route can have "
     "hundreds of trips per day across all service windows."),
    ("  STOP",
     "  A physical boarding and alighting location. Each stop has a unique stop_id, "
     "a name, and geographic coordinates. SF MUNI has 3,243 stops."),
    ("  SERVICE ID",
     "  A calendar key that determines which days a group of trips operates. "
     "Weekday, Saturday, or Sunday service maps to different headways."),
    ("  AVERAGE DAILY BOARDINGS",
     "  The mean number of passengers boarding a route on a given day type within a "
     "calendar month. This is the primary output metric the simulator reproduces."),
    ("  MODIFIER DATA",
     "  Supplementary datasets including Census population, LODES commute flows, "
     "land-use parcels, and ACS departure times that weight per-stop demand."),
    ("  SEASONAL INDEX",
     "  A monthly multiplier (Jan=0.88 to Jun=1.05) calibrated from historical SFMTA "
     "ridership trends to model month-to-month variation in synthetic output."),
    ("  PEAK BOOST",
     "  A demand multiplier of 1.35 applied during AM (7-9h) and PM (16-19h) windows "
     "to replicate the commute-hour surge seen in real SFMTA boarding data."),
    ("  TRIAL",
     "One completed simulation run representing a full synthetic year. Saved as a "
     "  folder of monthly txt files matching the real ridership schema."),
    ("  SIMULATION ENGINE",
     "  The QTimer-driven core loop advancing the clock 288 ticks per simulated day, "
     "updating vehicle positions, accumulating boardings, and flushing monthly "
     "  records through the Aggregator at day boundaries."),
    ("  VEHICLE",
     "  A simplified animated agent crawling between stops along a route, boarding "
     "waiting passengers up to its 60-seat capacity."),
    ("  AGGREGATOR",
     "  Collects per-day boarding tallies keyed by month, route, service category, "
     "and day type then averages them into monthly RidershipRecord objects."),
    ("  DAY TYPE",
     "  Weekday, Saturday, or Sunday - each carries its own demand multiplier."),
    ("  LAND USE",
     "  SF parcel classification from the 2023 assessor dataset. Residential share "
     "adjusts per-stop base demand; more homes near a stop means more riders."),
]


# DictionaryScreen: Scrollable glossary with a green left accent on each entry.
class DictionaryScreen(BaseScreen):

    def __init__(self, bus: EventBus, settings: dict, assets_root: str):
        self._assets_root = assets_root
        super().__init__(bus, settings)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_topbar())

        self._scroll = AppScrollArea()

        # Show a system overview image if one exists in the assets folder
        img_path = os.path.join(self._assets_root, "images", "system_overview.png")
        if os.path.exists(img_path):
            img_label = QLabel()
            pix = QPixmap(img_path)
            img_label.setPixmap(
                pix.scaledToWidth(700, Qt.TransformationMode.SmoothTransformation)
            )
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setStyleSheet("background: transparent; padding: 16px 0;")
            self._scroll.add_widget(img_label)

        for term, definition in _GLOSSARY:
            self._scroll.add_widget(self._make_entry(term, definition))

        root.addWidget(self._scroll, 1)

    def _make_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet(
            f"background-color: {THEME['surface']};"
            # Single subtle divider — not a bright white line
            "border-bottom: 1px solid #555555;"
        )
        hbox = QHBoxLayout(bar)
        hbox.setContentsMargins(16, 0, 16, 0)
        hbox.setSpacing(14)

        back_btn = SecondaryButton("[ < BACK ]")
        back_btn.setFixedWidth(110)
        back_btn.setFixedHeight(30)
        back_btn.clicked.connect(self._go_back)

        title = QLabel("// DICTIONARY")
        title.setStyleSheet(
            f"color: {THEME['primary']}; font-size: 13px; font-weight: bold;"
            f"font-family: {_MONO}; letter-spacing: 2px; background: transparent;"
        )

        hbox.addWidget(back_btn)
        hbox.addWidget(title)
        hbox.addStretch()
        return bar

    # _go_back: Walk the parent chain to reach AppController and navigate home.
    def _go_back(self):
        w = self
        while w.parent():
            w = w.parent()
        if hasattr(w, "screen_manager"):
            w.screen_manager.navigate(ScreenManager.START)

    # _make_entry: One glossary card with a green left accent and dark bottom border.
    def _make_entry(self, term: str, definition: str) -> QWidget:
        card = QWidget()
        card.setStyleSheet(
            f"background-color: {THEME['bg']};"
            # Dark separator — avoids the visual noise of bright white lines
            "border-bottom: 1px solid #2a2a2a;"
            f"border-left: 3px solid {THEME['primary']};"
        )
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(24, 16, 24, 16)
        vbox.setSpacing(8)

        term_lbl = QLabel(term)
        term_lbl.setStyleSheet(
            f"color: {THEME['primary']}; font-size: 14px; font-weight: bold;"
            f"font-family: {_MONO}; letter-spacing: 1px; background: transparent;"
        )

        def_lbl = QLabel(definition)
        def_lbl.setWordWrap(True)
        def_lbl.setStyleSheet(
            "color: #cccccc; font-size: 12px;"
            f"font-family: {_MONO}; background: transparent;"
        )

        vbox.addWidget(term_lbl)
        vbox.addWidget(def_lbl)
        return card
