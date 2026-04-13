# game_world_screen: Map canvas on the left, scrollable control panel on the right.

import os

from PyQt6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel,
                              QWidget, QSizePolicy, QScrollArea, QFrame)
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QPainter, QColor, QFont, QPen

from ui.base.base_screen            import BaseScreen
from ui.base.base_widget            import THEME
from ui.components.button           import PrimaryButton, SecondaryButton, DangerButton, IconButton
from ui.components.status_indicator import StatusDot
from app_controller.event_bus       import EventBus, Events
from app_controller.screen_manager  import ScreenManager

_MONO = "'Courier New', monospace"


# MapCanvas: QPainter surface that delegates all drawing to RendererAdapter.
class MapCanvas(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = None
        self.setMinimumSize(500, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: #050508;")

    # set_engine: Bind a simulation engine so paintEvent can call its renderer.
    def set_engine(self, engine):
        self._engine = engine

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#050508"))

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
            # Draw a faint pixel grid before the simulation starts
            pen = painter.pen()
            pen.setColor(QColor(0, 255, 136, 12))
            pen.setWidth(1)
            painter.setPen(pen)
            step = 20
            for x in range(0, self.width(), step):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), step):
                painter.drawLine(0, y, self.width(), y)

            painter.setPen(QColor(THEME["muted"]))
            painter.setFont(QFont("Courier New", 11))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "[ PRESS RUN TO INITIALISE THE SIMULATION ]",
            )
        painter.end()


# GameWorldScreen: Animated pixel map with a retro control panel sidebar.
class GameWorldScreen(BaseScreen):

    def __init__(self, bus: EventBus, settings: dict, app_controller):
        self._ctrl   = app_controller
        self._engine = None
        super().__init__(bus, settings)
        self.bus.subscribe(Events.SIM_TICK,      self._on_tick)
        self.bus.subscribe(Events.SIM_COMPLETED, self._on_completed)
        self.bus.subscribe(Events.SIM_ABORTED,   self._on_aborted)

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._canvas = MapCanvas()
        root.addWidget(self._canvas, 1)
        root.addWidget(self._build_panel())

    # _build_panel: Right-hand control strip with scroll safety for small windows.
    def _build_panel(self) -> QWidget:
        panel_width = 280

        outer = QWidget()
        outer.setFixedWidth(panel_width)
        outer.setStyleSheet(
            f"background: {THEME['bg']}; "
            "border-left: 2px solid #ffffff;"
        )
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Fixed header bar showing sim status
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(
            f"background: {THEME['surface']}; "
            f"border-bottom: 1px solid {THEME['border']};"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 0, 12, 0)

        self._status_dot = StatusDot(ready=False)
        self._status_lbl = QLabel("      SIMULATION")
        self._status_lbl.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        self._status_lbl.setStyleSheet(f"color: {THEME['accent']}; background: transparent;")

        self._run_state_lbl = QLabel("IDLE")
        self._run_state_lbl.setFont(QFont("Courier New", 9))
        self._run_state_lbl.setStyleSheet(f"color: {THEME['muted']}; background: transparent;")
        self._run_state_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        hl.addWidget(self._status_dot)
        hl.addSpacing(6)
        hl.addWidget(self._status_lbl)
        hl.addStretch()
        hl.addWidget(self._run_state_lbl)
        outer_layout.addWidget(header)

        # Scrollable content area so controls remain accessible on small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ background: {THEME['bg']}; border: none; }}"
            f"QScrollBar:vertical {{ width: 6px; background: {THEME['bg']}; }}"
            f"QScrollBar::handle:vertical {{ background: {THEME['border']}; border-radius: 3px; }}"
        )

        content = QWidget()
        content.setStyleSheet(f"background: {THEME['bg']};")
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # SIM DATE section
        vbox.addWidget(self._section_label("  // SIM DATE"))

        date_wrap = QWidget()
        date_wrap.setStyleSheet("background: transparent;")
        dw = QVBoxLayout(date_wrap)
        dw.setContentsMargins(14, 10, 14, 10)
        dw.setSpacing(6)

        self._date_lbl = QLabel("-")
        self._date_lbl.setFont(QFont("Courier New", 18, QFont.Weight.Bold))
        self._date_lbl.setStyleSheet(f"color: {THEME['accent']}; background: transparent;")
        self._date_lbl.setFixedHeight(26)

        self._day_type_lbl = QLabel("  WEEKDAY")
        self._day_type_lbl.setFont(QFont("Courier New", 9))
        self._day_type_lbl.setStyleSheet(f"color: {THEME['text']}; background: transparent;")
        self._day_type_lbl.setFixedHeight(16)

        # Manual progress bar so we can style it retro without QProgressBar chrome
        self._progress_bar_track = QWidget()
        self._progress_bar_track.setFixedHeight(6)
        self._progress_bar_track.setStyleSheet(f"background: {THEME['border']}; border: none;")
        self._progress_bar_inner = QWidget(self._progress_bar_track)
        self._progress_bar_inner.setGeometry(0, 0, 0, 6)
        self._progress_bar_inner.setStyleSheet(f"background: {THEME['accent']};")

        self._progress_lbl = QLabel("  0% OF YEAR")
        self._progress_lbl.setFont(QFont("Courier New", 9))
        self._progress_lbl.setStyleSheet(f"color: {THEME['muted']}; background: transparent;")
        self._progress_lbl.setFixedHeight(16)

        self._trial_lbl = QLabel("  TRIAL  -")
        self._trial_lbl.setFont(QFont("Courier New", 9))
        self._trial_lbl.setStyleSheet(f"color: {THEME['muted']}; background: transparent;")
        self._trial_lbl.setFixedHeight(16)

        dw.addWidget(self._date_lbl)
        dw.addWidget(self._day_type_lbl)
        dw.addSpacing(4)
        dw.addWidget(self._progress_bar_track)
        dw.addWidget(self._progress_lbl)
        dw.addWidget(self._trial_lbl)
        vbox.addWidget(date_wrap)

        # CONTROLS section
        vbox.addWidget(self._section_label("  // CONTROLS"))

        ctrl_wrap = QWidget()
        ctrl_wrap.setStyleSheet("background: transparent;")
        cw = QVBoxLayout(ctrl_wrap)
        cw.setContentsMargins(14, 10, 14, 10)
        cw.setSpacing(8)

        self._run_btn   = PrimaryButton("[ RUN ]")
        self._pause_btn = SecondaryButton("[ PAUSE ]")
        self._pause_btn.setEnabled(False)
        self._exit_btn  = DangerButton("[ EXIT TO START ]")

        self._run_btn.clicked.connect(self._on_run_clicked)
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        self._exit_btn.clicked.connect(self._on_exit_clicked)

        cw.addWidget(self._run_btn)
        cw.addWidget(self._pause_btn)
        cw.addWidget(self._exit_btn)
        vbox.addWidget(ctrl_wrap)

        # SPEED section
        vbox.addWidget(self._section_label("  // SPEED"))

        speed_wrap = QWidget()
        speed_wrap.setStyleSheet("background: transparent;")
        sw_layout = QHBoxLayout(speed_wrap)
        sw_layout.setContentsMargins(14, 10, 14, 10)
        sw_layout.setSpacing(6)

        self._speed_btns = []
        speeds = [1, 2, 5, 10, 20]
        for i, spd in enumerate(speeds):
            btn = IconButton(f"{spd}x")
            btn.setFixedSize(44, 30)
            btn.clicked.connect(lambda checked, idx=i: self._set_speed(idx))
            sw_layout.addWidget(btn)
            self._speed_btns.append(btn)

        # Default to the highest speed at startup
        self._highlight_speed(4)
        sw_layout.addStretch()
        vbox.addWidget(speed_wrap)

        # LIVE STATS section
        vbox.addWidget(self._section_label("  // LIVE STATS"))

        stats_wrap = QWidget()
        stats_wrap.setStyleSheet("background: transparent;")
        stats_layout = QVBoxLayout(stats_wrap)
        stats_layout.setContentsMargins(14, 10, 14, 10)
        stats_layout.setSpacing(6)

        self._vehicles_lbl  = QLabel("0")
        self._boardings_lbl = QLabel("0")
        self._routes_lbl    = QLabel("0")

        for key, val_lbl in [("  VEHICLES",     self._vehicles_lbl),
                              ("  BOARDINGS/DAY", self._boardings_lbl),
                              ("  ACTIVE ROUTES", self._routes_lbl)]:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row.setFixedHeight(22)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(0)

            key_lbl = QLabel(key)
            key_lbl.setFont(QFont("Courier New", 10))
            key_lbl.setStyleSheet(f"color: {THEME['text']}; background: transparent;")

            val_lbl.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
            val_lbl.setStyleSheet(f"color: {THEME['accent']}; background: transparent;")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            rl.addWidget(key_lbl)
            rl.addStretch()
            rl.addWidget(val_lbl)
            stats_layout.addWidget(row)

        vbox.addWidget(stats_wrap)

        # LEGEND section
        vbox.addWidget(self._section_label("  // LEGEND"))

        legend_wrap = QWidget()
        legend_wrap.setStyleSheet("background: transparent;")
        lw = QVBoxLayout(legend_wrap)
        lw.setContentsMargins(14, 10, 14, 10)
        lw.setSpacing(10)

        legend_items = [
            ("#2a6abf", "   BUS"),
            ("#bf8a20", "   TRAM"),
            ("#7a2aaf", "   CABLE CAR"),
            ("#af2a3a", "   METRO"),
        ]
        for hex_col, label in legend_items:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row.setFixedHeight(22)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(10)

            dot = QWidget()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"background: {hex_col};")

            lbl = QLabel(label)
            lbl.setFont(QFont("Courier New", 10))
            lbl.setStyleSheet(f"color: {THEME['text']}; background: transparent;")

            rl.addWidget(dot)
            rl.addWidget(lbl)
            rl.addStretch()
            lw.addWidget(row)

        vbox.addWidget(legend_wrap)
        vbox.addStretch()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        return outer

    # _section_label: Green header bar for panel sections with subtle dark borders.
    def _section_label(self, text: str) -> QWidget:
        wrap = QWidget()
        wrap.setFixedHeight(28)
        wrap.setStyleSheet(
            f"background: {THEME['surface']}; "
            f"border-bottom: 1px solid {THEME['border']}; "
            f"border-top: 1px solid {THEME['border']};"
        )
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(14, 0, 14, 0)
        lbl = QLabel(text)
        lbl.setFont(QFont("Courier New", 9))
        lbl.setStyleSheet(
            f"color: {THEME['primary']}; background: transparent; letter-spacing: 2px;"
        )
        layout.addWidget(lbl)
        return wrap

    # _highlight_speed: Style the active speed button with a green fill.
    def _highlight_speed(self, idx: int):
        for i, btn in enumerate(self._speed_btns):
            if i == idx:
                btn.setStyleSheet(
                    f"QPushButton {{ "
                    f"background: {THEME['accent']}; color: #000; "
                    f"font-family: {_MONO}; font-size: 10px; "
                    "font-weight: bold; border: none; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ "
                    f"background: {THEME['bg']}; color: #888; "
                    f"font-family: {_MONO}; font-size: 10px; "
                    "border: 1px solid #333; }} "
                    f"QPushButton:hover {{ "
                    f"border-color: {THEME['primary']}; "
                    f"color: {THEME['primary']}; }}"
                )

    # _set_speed: Change speed multiplier and update button highlighting.
    def _set_speed(self, idx: int):
        if self._engine:
            self._engine.set_speed(idx)
        self._highlight_speed(idx)

    # _on_run_clicked: Build a fresh SimulationEngine and start the loop.
    def _on_run_clicked(self):
        from game_world.core.simulation_engine import SimulationEngine

        if self._engine and self._engine.is_running():
            self._engine.abort()

        trial_num = self._ctrl.next_trial_number()
        self._trial_lbl.setText(f"TRIAL  {trial_num:03d}")

        # Resolve config path whether launched from SD_Game/ or the repo root
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
        self._run_state_lbl.setText("RUNNING")

    # _on_pause_clicked: Toggle between paused and running states.
    def _on_pause_clicked(self):
        if not self._engine:
            return
        if self._engine.is_running():
            self._engine.pause()
            self._pause_btn.setText("[ RESUME ]")
            self._status_dot.set_ready(False)
            self._run_state_lbl.setText("PAUSED")
        else:
            self._engine.resume()
            self._pause_btn.setText("[ PAUSE ]")
            self._status_dot.set_ready(True)
            self._run_state_lbl.setText("RUNNING")

    # _on_exit_clicked: Stop the simulation and return to the start screen.
    def _on_exit_clicked(self):
        if self._engine and self._engine.is_running():
            self._engine.abort()
        self._engine = None
        self._canvas.set_engine(None)
        self._canvas.update()

        self._run_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._pause_btn.setText("[ PAUSE ]")
        self._status_dot.set_ready(False)
        self._run_state_lbl.setText("IDLE")
        self._date_lbl.setText("-")

        self._ctrl.screen_manager.navigate(ScreenManager.START)

    # _on_tick: Repaint canvas and update all live labels each sim tick.
    def _on_tick(self, engine):
        self._canvas.update()
        if not engine:
            return

        self._date_lbl.setText(engine.date_label())
        try:
            self._day_type_lbl.setText(engine._time.day_type().upper())
        except Exception:
            pass

        pct     = int(engine.progress() * 100)
        track_w = self._progress_bar_track.width()
        fill_w  = int(track_w * engine.progress())
        self._progress_lbl.setText(f"  {pct}% OF YEAR")
        self._progress_bar_inner.setGeometry(0, 0, fill_w, 6)

        n_v     = len(engine.vehicles)
        n_r     = len(engine.routes)
        total_b = sum(r.daily_boardings for r in engine.routes)
        self._vehicles_lbl.setText(str(n_v))
        self._boardings_lbl.setText(f"{total_b:,}")
        self._routes_lbl.setText(str(n_r))

    # _on_completed: Update UI when the full year finishes successfully.
    def _on_completed(self, result):
        self._run_state_lbl.setText("DONE")
        self._status_dot.set_ready(False)
        self._run_btn.setEnabled(True)
        self._run_btn.setText("[ RUN AGAIN ]")
        self._pause_btn.setEnabled(False)

    # _on_aborted: Reset panel to idle when the user cancels mid-run.
    def _on_aborted(self, _=None):
        self._run_state_lbl.setText("ABORTED")
        self._status_dot.set_ready(False)
        self._run_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
