# loading_screen: Retro splash screen with progress bar shown at application start.

from PyQt6.QtWidgets import QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QFont

from ui.base.base_screen  import BaseScreen
from ui.base.base_widget  import THEME
from app_controller.event_bus import EventBus


# LoadingScreen: Animates a progress bar then signals the controller when done.
class LoadingScreen(BaseScreen):

    def __init__(self, bus: EventBus, settings: dict):
        self._progress_val = 0
        self._tick_timer   = None
        super().__init__(bus, settings)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        title = QLabel(self.settings["app"]["title"].upper())
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {THEME['primary']}; font-size: 32px; font-weight: bold;"
            f"font-family: {THEME['font']}; letter-spacing: 4px;"
            "background: transparent;"
        )

        sub = QLabel("// INITIALISING SIMULATION ENVIRONMENT")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            f"color: {THEME['muted']}; font-size: 10px; letter-spacing: 2px;"
            f"font-family: {THEME['font']}; background: transparent;"
        )

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedWidth(360)
        self._bar.setFixedHeight(4)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {THEME['surface']};
                border: 1px solid {THEME['border']};
                border-radius: 0px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME['primary']};
                border-radius: 0px;
            }}
        """)

        self._pct_lbl = QLabel("0%")
        self._pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pct_lbl.setStyleSheet(
            f"color: {THEME['muted']}; font-size: 10px; font-family: {THEME['font']};"
            "background: transparent;"
        )

        version = QLabel(f"v{self.settings['app']['version']}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(
            f"color: {THEME['border']}; font-size: 10px; font-family: {THEME['font']};"
            "background: transparent;"
        )

        layout.addStretch(2)
        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(sub)
        layout.addSpacing(20)
        layout.addWidget(self._bar, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._pct_lbl)
        layout.addStretch(2)
        layout.addWidget(version)
        layout.addSpacing(16)

        # Divide the loading duration into 100 equal ticks
        duration_ms = self.settings["app"].get("loading_duration_ms", 2500)
        interval_ms = max(30, duration_ms // 100)
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(interval_ms)
        self._tick_timer.timeout.connect(self._advance_bar)
        self._tick_timer.start()

    # _advance_bar: Increment the progress bar by one percent per tick.
    def _advance_bar(self):
        self._progress_val = min(self._progress_val + 1, 100)
        self._bar.setValue(self._progress_val)
        self._pct_lbl.setText(f"{self._progress_val}%")

    # stop_animation: Halt the timer before transitioning to the start screen.
    def stop_animation(self):
        if self._tick_timer:
            self._tick_timer.stop()
