"""
Filename: loading_screen.py
Author: Ayemhenre Isikhuemhen
Description: Mini splash screen shown at launch — animated progress bar fades
             into the Start screen after a configurable duration.
Last Updated: March, 2026
"""

# Libraries
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Modules
from ui.base.base_screen import BaseScreen
from ui.base.base_widget import THEME
from app_controller.event_bus import EventBus


# LoadingScreen: Splash shown while the application initialises
class LoadingScreen(BaseScreen):

    # __init__ (bus, settings)
    def __init__(self, bus: EventBus, settings: dict):
        self._progress_val = 0
        self._tick_timer   = None
        super().__init__(bus, settings)

    # _build: Lay out the title, subtitle, and progress bar
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        title = QLabel(self.settings["app"]["title"])
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {THEME['accent']}; background: transparent;")

        sub = QLabel("Initialising simulation environment…")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {THEME['muted']}; font-size: 13px; background: transparent;")

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedWidth(340)
        self._bar.setFixedHeight(6)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {THEME['border']};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME['accent']};
                border-radius: 3px;
            }}
        """)

        version = QLabel(f"v{self.settings['app']['version']}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"color: {THEME['border']}; font-size: 11px; background: transparent;")

        layout.addStretch(2)
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addWidget(self._bar, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        layout.addStretch(3)

        duration_ms = self.settings["app"].get("loading_duration_ms", 2500)
        interval_ms = max(30, duration_ms // 100)
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(interval_ms)
        self._tick_timer.timeout.connect(self._advance_bar)
        self._tick_timer.start()

    # _advance_bar: Increment progress each timer tick
    def _advance_bar(self):
        self._progress_val = min(self._progress_val + 1, 100)
        self._bar.setValue(self._progress_val)

    # stop_animation: Halt the tick timer when transitioning away
    def stop_animation(self):
        if self._tick_timer:
            self._tick_timer.stop()