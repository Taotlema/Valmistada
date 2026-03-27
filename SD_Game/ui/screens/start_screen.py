"""
Filename: start_screen.py
Author: Ayemhenre Isikhuemhen
Description: Start screen — project title, navigation buttons, batch/modifier
             status indicators, stat dashboard, and a modifier toggle.
Last Updated: March, 2026
"""

# Libraries
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                              QCheckBox, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Modules
from ui.base.base_screen import BaseScreen
from ui.base.base_widget import THEME
from ui.components.button import PrimaryButton, SecondaryButton
from ui.components.status_indicator import StatusIndicator
from ui.components.dashboard_widget import DashboardWidget
from app_controller.event_bus import EventBus, Events
from app_controller.screen_manager import ScreenManager


# StartScreen: Entry hub after the loading splash clears
class StartScreen(BaseScreen):

    # __init__ (bus, settings, app_controller)
    def __init__(self, bus: EventBus, settings: dict, app_controller):
        self._ctrl = app_controller
        super().__init__(bus, settings)
        self.bus.subscribe(Events.GTFS_LOADED, lambda _: self._refresh_status())
        self.bus.subscribe(Events.TRIAL_SAVED, lambda _: self._refresh_status())

    # _build: Full start-screen layout
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 50, 60, 40)
        root.setSpacing(0)

        title = QLabel(self.settings["app"]["title"])
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {THEME['accent']}; background: transparent;")

        tagline = QLabel("A transit ridership simulation engine for SFMTA")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet(f"color: {THEME['muted']}; font-size: 13px; background: transparent;")

        root.addWidget(title)
        root.addSpacing(6)
        root.addWidget(tagline)
        root.addSpacing(30)

        # Status row
        status_row = QWidget()
        status_row.setStyleSheet("background: transparent;")
        sr = QHBoxLayout(status_row)
        sr.setContentsMargins(0, 0, 0, 0)
        sr.setSpacing(24)
        sr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._batch_ind    = StatusIndicator("Batch files ready",    ready=False)
        self._modifier_ind = StatusIndicator("Modifier files ready", ready=False)
        sr.addWidget(self._batch_ind)
        sr.addWidget(self._modifier_ind)
        root.addWidget(status_row)
        root.addSpacing(20)

        # Dashboard
        self._dashboard = DashboardWidget()
        root.addWidget(self._dashboard)
        root.addSpacing(28)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {THEME['border']};")
        root.addWidget(divider)
        root.addSpacing(24)

        # Nav buttons
        nav_row = QWidget()
        nav_row.setStyleSheet("background: transparent;")
        nav = QHBoxLayout(nav_row)
        nav.setContentsMargins(0, 0, 0, 0)
        nav.setSpacing(14)
        nav.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_input  = SecondaryButton("📂  Input Data")
        btn_output = SecondaryButton("📊  Output Data")
        btn_dict   = SecondaryButton("📖  Dictionary")
        btn_run    = PrimaryButton("▶  Run Simulation")

        for btn in [btn_input, btn_output, btn_dict]:
            btn.setFixedWidth(160)
        btn_run.setFixedWidth(180)

        btn_input.clicked.connect(
            lambda: self._ctrl.screen_manager.navigate(ScreenManager.INPUT))
        btn_output.clicked.connect(
            lambda: self._ctrl.screen_manager.navigate(ScreenManager.OUTPUT))
        btn_dict.clicked.connect(
            lambda: self._ctrl.screen_manager.navigate(ScreenManager.DICTIONARY))
        btn_run.clicked.connect(self._go_to_game_world)

        nav.addWidget(btn_input)
        nav.addWidget(btn_output)
        nav.addWidget(btn_dict)
        nav.addSpacing(20)
        nav.addWidget(btn_run)
        root.addWidget(nav_row)
        root.addSpacing(28)

        # Modifier toggle
        toggle_row = QWidget()
        toggle_row.setStyleSheet("background: transparent;")
        tl = QHBoxLayout(toggle_row)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._modifier_toggle = QCheckBox("Apply modifier files to simulation")
        self._modifier_toggle.setChecked(True)
        self._modifier_toggle.setStyleSheet(f"""
            QCheckBox {{ color: {THEME['muted']}; font-size: 12px; }}
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border: 1px solid {THEME['border']};
                border-radius: 3px;
                background: {THEME['surface']};
            }}
            QCheckBox::indicator:checked {{
                background: {THEME['primary']};
                border-color: {THEME['primary']};
            }}
        """)
        tl.addWidget(self._modifier_toggle)
        root.addWidget(toggle_row)
        root.addStretch()

    # on_enter: Refresh indicators whenever this screen becomes visible
    def on_enter(self):
        self._refresh_status()

    # _refresh_status: Pull live state from the app controller
    def _refresh_status(self):
        batch_ok    = self._ctrl.is_batch_ready()
        modifier_ok = self._ctrl.is_modifier_ready()
        self._batch_ind.set_ready(
            batch_ok, "Batch files ready" if batch_ok else "No batch loaded"
        )
        self._modifier_ind.set_ready(
            modifier_ok, "Modifier files ready" if modifier_ok else "Modifier missing"
        )
        self._dashboard.refresh(self._ctrl)

    # _go_to_game_world: Auto-load SF feed if needed, then navigate
    def _go_to_game_world(self):
        import os
        if not self._ctrl.is_batch_ready():
            gtfs_dir = os.path.join(
                self._ctrl.gtfs_root, "San Francisco (muni_gtfs-current)"
            )
            if os.path.isdir(gtfs_dir):
                self._ctrl.load_city_feed("San Francisco", gtfs_dir)
        self._ctrl.screen_manager.navigate(ScreenManager.GAME_WORLD)

    # modifier_enabled: Whether the user wants modifier data applied
    def modifier_enabled(self) -> bool:
        return self._modifier_toggle.isChecked()