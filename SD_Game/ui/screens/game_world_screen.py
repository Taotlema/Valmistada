"""
Filename: game_world_screen.py
Author: Ayemhenre Isikhuemhen
Description: Game world screen — animated map canvas on the left, control panel
             on the right with run/pause, speed controls, sim date, and status.
Last Updated: March, 2026
"""

# Libraries
import os
from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel,
                              QWidget, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont

# Modules
from ui.base.base_screen import BaseScreen
from ui.base.base_widget import THEME
from ui.components.button import PrimaryButton, SecondaryButton, DangerButton, IconButton
from ui.components.status_indicator import StatusDot
from app_controller.event_bus import EventBus, Events
from app_controller.screen_manager import ScreenManager


# MapCanvas: QPainter surface that delegates rendering to the sim engine's renderer
class MapCanvas(QWidget):

    # __init__ (parent)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = None
        self.setMinimumSize(500, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: #0D1117;")

    # set_engine (engine): Bind the simulation engine for render access
    def set_engine(self, engine):
        self._engine = engine

    # paintEvent: Ask the renderer to draw the current sim state
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0D1117"))

        if self._engine and self._engine.renderer:
            self._engine.renderer.render(
                painter,
                self._engine.routes,
                self._engine.stations,
                self._engine.vehicles,
                self.width(),
                self.height(),
            )
        else:
            painter.setPen(QColor(THEME["muted"]))
            painter.setFont(QFont("Segoe UI", 13))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Press RUN to initialise the simulation"
            )
        painter.end()


# GameWorldScreen: Full simulation screen — map + control panel
class GameWorldScreen(BaseScreen):

    # __init__ (bus, settings, app_controller)
    def __init__(self, bus: EventBus, settings: dict, app_controller):
        self._ctrl   = app_controller
        self._engine = None
        super().__init__(bus, settings)
        self.bus.subscribe(Events.SIM_TICK,      self._on_tick)
        self.bus.subscribe(Events.SIM_COMPLETED, self._on_completed)
        self.bus.subscribe(Events.SIM_ABORTED,   self._on_aborted)

    # _build: Split layout — map canvas left, control panel right
    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._canvas = MapCanvas()
        root.addWidget(self._canvas, 1)
        root.addWidget(self._build_panel())

    # _build_panel: All controls in a fixed-width vertical strip
    def _build_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(240)
        panel.setStyleSheet(f"""
            background-color: {THEME['surface']};
            border-left: 1px solid {THEME['border']};
        """)
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(16, 20, 16, 20)
        vbox.setSpacing(14)

        title = QLabel("Simulation")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {THEME['text']}; background: transparent;")
        vbox.addWidget(title)

        # Status dot + label
        status_row = QWidget()
        status_row.setStyleSheet("background: transparent;")
        sr = QHBoxLayout(status_row)
        sr.setContentsMargins(0, 0, 0, 0)
        sr.setSpacing(8)
        self._status_dot = StatusDot(ready=False)
        self._status_lbl = QLabel("Idle")
        self._status_lbl.setStyleSheet(f"color: {THEME['muted']}; font-size: 12px;")
        sr.addWidget(self._status_dot)
        sr.addWidget(self._status_lbl)
        sr.addStretch()
        vbox.addWidget(status_row)

        # Sim date
        self._date_lbl = QLabel("—")
        self._date_lbl.setStyleSheet(
            f"color: {THEME['accent']}; font-size: 12px; background: transparent;"
        )
        self._date_lbl.setWordWrap(True)
        vbox.addWidget(self._date_lbl)

        self._progress_lbl = QLabel("Progress: 0%")
        self._progress_lbl.setStyleSheet(
            f"color: {THEME['muted']}; font-size: 11px; background: transparent;"
        )
        vbox.addWidget(self._progress_lbl)

        vbox.addWidget(self._make_divider())

        # Run / Pause buttons
        self._run_btn = PrimaryButton("▶  Run")
        self._run_btn.setFixedHeight(40)
        self._run_btn.clicked.connect(self._on_run_clicked)
        vbox.addWidget(self._run_btn)

        self._pause_btn = SecondaryButton("⏸  Pause")
        self._pause_btn.setFixedHeight(36)
        self._pause_btn.setEnabled(False)
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        vbox.addWidget(self._pause_btn)

        vbox.addWidget(self._make_divider())

        # Speed controls
        spd_lbl = QLabel("Speed")
        spd_lbl.setStyleSheet(
            f"color: {THEME['muted']}; font-size: 11px; font-weight: 600; background: transparent;"
        )
        vbox.addWidget(spd_lbl)

        speed_row = QWidget()
        speed_row.setStyleSheet("background: transparent;")
        sr2 = QHBoxLayout(speed_row)
        sr2.setContentsMargins(0, 0, 0, 0)
        sr2.setSpacing(6)

        self._speed_btns = []
        for i, label in enumerate(["1×", "2×", "5×", "10×", "20×"]):
            btn = IconButton(label, size=38)
            btn.clicked.connect(lambda _, idx=i: self._set_speed(idx))
            sr2.addWidget(btn)
            self._speed_btns.append(btn)

        vbox.addWidget(speed_row)
        self._highlight_speed(0)

        vbox.addWidget(self._make_divider())

        self._trial_lbl = QLabel("Trial  —")
        self._trial_lbl.setStyleSheet(
            f"color: {THEME['muted']}; font-size: 12px; background: transparent;"
        )
        vbox.addWidget(self._trial_lbl)
        vbox.addStretch()

        # Exit button
        exit_btn = DangerButton("✕  Exit to Start")
        exit_btn.setFixedHeight(36)
        exit_btn.clicked.connect(self._on_exit_clicked)
        vbox.addWidget(exit_btn)

        return panel

    # _make_divider: Thin horizontal rule
    def _make_divider(self) -> QFrame:
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {THEME['border']}; border: none;")
        return div

    # on_enter: Reset panel state each time the screen is visited
    def on_enter(self):
        self._date_lbl.setText("—")
        self._progress_lbl.setText("Progress: 0%")
        self._status_dot.set_ready(False)
        self._status_lbl.setText("Idle")
        self._run_btn.setEnabled(True)
        self._run_btn.setText("▶  Run")
        self._pause_btn.setEnabled(False)
        self._canvas.set_engine(None)
        self._canvas.update()

    # _on_run_clicked: Build a fresh SimulationEngine and start it
    def _on_run_clicked(self):
        from game_world.core.simulation_engine import SimulationEngine

        if self._engine and self._engine.is_running():
            self._engine.abort()

        trial_num = self._ctrl.next_trial_number()
        self._trial_lbl.setText(f"Trial  {trial_num}")

        # Resolve config path regardless of launch directory
        cfg_path = os.path.join("SD_Game", "config", "simulation_config.yaml")
        if not os.path.exists(cfg_path):
            cfg_path = os.path.join("config", "simulation_config.yaml")

        self._engine = SimulationEngine(
            bus=self.bus,
            app_controller=self._ctrl,
            sim_config_path=cfg_path,
            trial_number=trial_num,
        )

        if self._ctrl.feeds:
            city = list(self._ctrl.feeds.keys())[0]
        else:
            sf_dir = os.path.join(
                self._ctrl.gtfs_root, "San Francisco (muni_gtfs-current)"
            )
            self._ctrl.load_city_feed("San Francisco", sf_dir)
            city = "San Francisco"

        self._engine.build_world(city, self._canvas.width(), self._canvas.height())
        self._canvas.set_engine(self._engine)
        self._engine.start()

        self._run_btn.setEnabled(False)
        self._pause_btn.setEnabled(True)
        self._status_dot.set_ready(True)
        self._status_lbl.setText("Running")

    # _on_pause_clicked: Toggle pause / resume
    def _on_pause_clicked(self):
        if not self._engine:
            return
        if self._engine.is_running():
            self._engine.pause()
            self._pause_btn.setText("▶  Resume")
            self._status_dot.set_ready(False)
            self._status_lbl.setText("Paused")
        else:
            self._engine.resume()
            self._pause_btn.setText("⏸  Pause")
            self._status_dot.set_ready(True)
            self._status_lbl.setText("Running")

    # _set_speed (idx): Change sim speed and highlight the active button
    def _set_speed(self, idx: int):
        if self._engine:
            self._engine.set_speed(idx)
        self._highlight_speed(idx)

    # _highlight_speed (idx): Style the active speed button differently
    def _highlight_speed(self, idx: int):
        for i, btn in enumerate(self._speed_btns):
            if i == idx:
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        border-radius: 4px; font-size: 12px; font-weight: 700;
                        border: 1px solid {THEME['primary']};
                        color: #fff;
                        background-color: {THEME['primary']};
                    }}
                    """
                )
            else:
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        border-radius: 4px; font-size: 12px; font-weight: 700;
                        border: 1px solid {THEME['border']};
                        color: {THEME['text']};
                        background-color: {THEME['surface']};
                    }}
                    QPushButton:hover {{ background-color: {THEME['border']}; }}
                    """
                )

    # _on_exit_clicked: Abort any running sim and return to start
    def _on_exit_clicked(self):
        if self._engine and self._engine.is_running():
            self._engine.abort()
        self._engine = None
        self._canvas.set_engine(None)
        self._ctrl.screen_manager.navigate(ScreenManager.START)

    # _on_tick (engine): Repaint canvas and update date/progress labels
    def _on_tick(self, engine):
        self._canvas.update()
        if engine:
            self._date_lbl.setText(engine.date_label())
            pct = int(engine.progress() * 100)
            self._progress_lbl.setText(f"Progress: {pct}%")

    # _on_completed (trial_result): Update UI when sim finishes
    def _on_completed(self, _result):
        self._status_dot.set_ready(False)
        self._status_lbl.setText("Complete")
        self._run_btn.setEnabled(True)
        self._run_btn.setText("▶  Run Again")
        self._pause_btn.setEnabled(False)
        self._progress_lbl.setText("Progress: 100%")

    # _on_aborted: Reset panel to idle state
    def _on_aborted(self):
        self._status_dot.set_ready(False)
        self._status_lbl.setText("Aborted")
        self._run_btn.setEnabled(True)
        self._run_btn.setText("▶  Run")
        self._pause_btn.setEnabled(False)