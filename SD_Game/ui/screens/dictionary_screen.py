"""
Filename: dictionary_screen.py
Author: Ayemhenre Isikhuemhen
Description: Dictionary screen — optional system-overview image followed by
             scrollable glossary of simulator terminology.
Last Updated: March, 2026
"""

# Libraries
import os
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                              QWidget, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

# Modules
from ui.base.base_screen import BaseScreen
from ui.base.base_widget import THEME
from ui.components.button import SecondaryButton
from ui.components.scroll_area import AppScrollArea
from app_controller.event_bus import EventBus
from app_controller.screen_manager import ScreenManager


_GLOSSARY = [
    ("GTFS",
     "General Transit Feed Specification — an open standard for publishing public "
     "transit schedules and geographic data. This simulator ingests GTFS .txt files "
     "to model the real network topology."),
    ("Route",
     "A named transit service line (e.g. 1 California) operating between two "
     "termini with a fixed sequence of stops. Route types: 0=Tram, 1=Subway, "
     "3=Bus, 5=Cable Car."),
    ("Trip",
     "A single scheduled traversal of a route on a particular service day. One route "
     "may have hundreds of trips per day across all service windows."),
    ("Stop",
     "A physical location where passengers board or alight. Each stop has a unique "
     "stop_id, a name, and geographic coordinates. SF Muni has 3,243 stops."),
    ("Service ID",
     "A calendar key that determines which days a group of trips operates — Weekday, "
     "Saturday, or Sunday service windows map to different headways and vehicle counts."),
    ("Average Daily Boardings",
     "The mean number of passengers boarding a route on a given day type within a "
     "calendar month. This is the primary output metric the simulator reproduces."),
    ("Modifier Data",
     "Supplementary datasets (Census population, LODES commute flows, land-use parcels, "
     "ACS departure times) that weight per-stop demand. Higher residential density "
     "means higher base boardings."),
    ("Seasonal Index",
     "A monthly multiplier (January=0.88 … June=1.05) calibrated from historical "
     "SFMTA ridership trends to model month-to-month variation in synthetic output."),
    ("Peak Boost",
     "A demand multiplier (×1.35) applied during AM (7–9h) and PM (16–19h) windows "
     "to replicate the commute-hour surge in real SFMTA boarding data."),
    ("Trial",
     "One completed simulation run representing a full synthetic year. Each trial is "
     "saved as a folder of monthly .txt files matching the real ridership schema: "
     "Month, Route, Service Category, Service Day of the Week, Average Daily Boardings."),
    ("Simulation Engine",
     "The QTimer-driven core loop advancing the clock 288 ticks per simulated day "
     "(5-minute intervals), updating vehicle positions, accumulating boardings, and "
     "flushing monthly records through the Aggregator at day boundaries."),
    ("Vehicle (Worm)",
     "A simplistic animated agent crawling between stops along a route, boarding "
     "waiting passengers up to its 60-seat capacity. Three vehicles per route during "
     "peak windows, one off-peak."),
    ("Aggregator",
     "The data pipeline component that collects per-day boarding tallies keyed by "
     "(month, route, service category, day type) and averages them into the monthly "
     "RidershipRecord objects written to disk at trial end."),
    ("Day Type",
     "The service-calendar category for a simulated date: Weekday, Saturday, or Sunday. "
     "Each type carries its own demand multiplier drawn from SFMTA modifier data."),
    ("Land Use",
     "SF parcel classification (RESIDENT, MIXRES, RETAIL/ENT, MIPS, etc.) from the "
     "2023 assessor dataset. Residential share adjusts per-stop base demand — "
     "more homes near a stop means more walk-on riders."),
]


# DictionaryScreen: Reference page with an optional diagram and a full glossary
class DictionaryScreen(BaseScreen):

    # __init__ (bus, settings, assets_root)
    def __init__(self, bus: EventBus, settings: dict, assets_root: str):
        self._assets_root = assets_root
        super().__init__(bus, settings)

    # _build: Top bar, optional image, glossary entries in a scroll area
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_topbar())

        self._scroll = AppScrollArea()

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

        heading = QLabel("Terminology & Concepts")
        heading.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        heading.setStyleSheet(
            f"color: {THEME['text']}; background: transparent; padding: 14px 24px 6px 24px;"
        )
        self._scroll.add_widget(heading)

        for term, definition in _GLOSSARY:
            self._scroll.add_widget(self._make_entry(term, definition))

        root.addWidget(self._scroll, 1)

    # _make_topbar: Title + back
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
        back_btn.clicked.connect(self._go_back)

        title = QLabel("Dictionary")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {THEME['text']}; background: transparent;")

        hbox.addWidget(back_btn)
        hbox.addSpacing(16)
        hbox.addWidget(title)
        hbox.addStretch()
        return bar

    # _go_back: Navigate to start screen
    def _go_back(self):
        w = self
        while w.parent():
            w = w.parent()
        if hasattr(w, "screen_manager"):
            w.screen_manager.navigate(ScreenManager.START)

    # _make_entry (term, definition): Styled glossary card
    def _make_entry(self, term: str, definition: str) -> QWidget:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['surface']};
                border: 1px solid {THEME['border']};
                border-radius: 6px;
                margin: 2px 24px;
            }}
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(16, 12, 16, 12)
        vbox.setSpacing(4)

        term_lbl = QLabel(term)
        term_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        term_lbl.setStyleSheet(f"color: {THEME['accent']}; background: transparent;")

        def_lbl = QLabel(definition)
        def_lbl.setWordWrap(True)
        def_lbl.setStyleSheet(
            f"color: {THEME['muted']}; font-size: 12px; background: transparent;"
        )

        vbox.addWidget(term_lbl)
        vbox.addWidget(def_lbl)
        return card