# start_screen: Title, 2x2 nav grid filling full height, status sidebar unchanged.

import os

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QCheckBox, QWidget, QPushButton)
from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QFont

from ui.base.base_screen            import BaseScreen
from ui.base.base_widget            import THEME
from ui.components.button           import PrimaryButton, SecondaryButton
from ui.components.status_indicator import StatusIndicator
from ui.components.dashboard_widget import DashboardWidget
from app_controller.event_bus       import EventBus, Events
from app_controller.screen_manager  import ScreenManager

_MONO = THEME["font"]
_G    = THEME["primary"]
_W    = "#e0e0e0"
_M    = "#777777"


# StartScreen: Left hero+nav grid, right status sidebar; no top header bar.
class StartScreen(BaseScreen):

    def __init__(self, bus: EventBus, settings: dict, app_controller):
        self._ctrl = app_controller
        super().__init__(bus, settings)
        self.bus.subscribe(Events.GTFS_LOADED, lambda _: self._refresh_status())
        self.bus.subscribe(Events.TRIAL_SAVED, lambda _: self._refresh_status())

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left column: hero block + nav grid filling all remaining height
        left = QWidget()
        left.setStyleSheet(f"background: {THEME['bg']};")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Hero block with title and version
        hero = QWidget()
        hero.setStyleSheet(f"background: {THEME['surface']};")
        hv = QVBoxLayout(hero)
        hv.setContentsMargins(48, 36, 48, 36)
        hv.setSpacing(6)

        title = QLabel(self.settings["app"]["title"].upper())
        title.setFont(QFont("Courier New", 36, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {_G}; background: transparent;")
        hv.addWidget(title)

        desc = QLabel("SYNTHETIC DATA RESEARCH")
        desc.setFont(QFont("Courier New", 11))
        desc.setStyleSheet(f"color: {_W}; background: transparent; letter-spacing: 2px;")
        hv.addWidget(desc)

        ver = QLabel(f"V {self.settings['app'].get('version', '1.0.0')}")
        ver.setFont(QFont("Courier New", 10))
        ver.setStyleSheet(f"color: {_M}; background: transparent; letter-spacing: 1px;")
        hv.addWidget(ver)

        left_layout.addWidget(hero)

        # Single subtle separator between hero and grid — no bright white line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #2a2a2a; border: none;")
        left_layout.addWidget(sep)

        # 2x2 nav grid; stretch=1 makes it fill all space below the hero block
        nav_container = QWidget()
        nav_container.setStyleSheet(f"background: {THEME['bg']};")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        col1 = QVBoxLayout()
        col1.setSpacing(0)
        col1.setContentsMargins(0, 0, 0, 0)
        col2 = QVBoxLayout()
        col2.setSpacing(0)
        col2.setContentsMargins(0, 0, 0, 0)

        btn_input  = self._make_nav_cell("[>]", "INPUT DATA",     "Manage GTFS feeds",
                                          lambda: self._ctrl.screen_manager.navigate(ScreenManager.INPUT))
        btn_dict   = self._make_nav_cell("[?]", "DICTIONARY",     "Terminology guide",
                                          lambda: self._ctrl.screen_manager.navigate(ScreenManager.DICTIONARY))
        btn_output = self._make_nav_cell("[=]", "OUTPUT DATA",    "Browse trial results",
                                          lambda: self._ctrl.screen_manager.navigate(ScreenManager.OUTPUT))
        btn_sim    = self._make_nav_cell("[*]", "RUN SIMULATION", "Launch game world",
                                          self._go_to_game_world, primary=True)

        # Primary cell gets a subtle green border at rest; all others are dark
        col1.addWidget(btn_input, 1)
        col1.addWidget(btn_dict, 1)
        col2.addWidget(btn_output, 1)
        col2.addWidget(btn_sim, 1)

        nav_layout.addLayout(col1)

        # Dark vertical divider between columns
        vd = QFrame()
        vd.setFrameShape(QFrame.Shape.VLine)
        vd.setFixedWidth(1)
        vd.setStyleSheet("background-color: #2a2a2a; border: none;")
        nav_layout.addWidget(vd)
        nav_layout.addLayout(col2)

        left_layout.addWidget(nav_container, 1)
        root.addWidget(left, 3)

        # Right column: status sidebar — unchanged from earlier iteration
        right = QWidget()
        right.setStyleSheet(
            f"background: {THEME['surface']}; "
            f"border-left: 1px solid {THEME['border']};"
        )
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        right_layout.addWidget(self._make_section_header("// SYSTEM STATUS"))

        status_wrap = QWidget()
        status_wrap.setStyleSheet("background: transparent;")
        sw = QVBoxLayout(status_wrap)
        sw.setContentsMargins(16, 14, 16, 14)
        sw.setSpacing(12)
        self._batch_ind    = StatusIndicator("BATCH FILES READY",    ready=False)
        self._modifier_ind = StatusIndicator("MODIFIER DATA LOADED", ready=False)
        self._trials_ind   = StatusIndicator("NO TRIALS RUN YET",    ready=False)
        sw.addWidget(self._batch_ind)
        sw.addWidget(self._modifier_ind)
        sw.addWidget(self._trials_ind)
        right_layout.addWidget(status_wrap)

        right_layout.addWidget(self._make_section_header("// SESSION STATS"))
        self._dashboard = DashboardWidget()
        dash_wrap = QWidget()
        dash_wrap.setStyleSheet("background: transparent;")
        dv = QVBoxLayout(dash_wrap)
        dv.setContentsMargins(16, 14, 16, 14)
        dv.addWidget(self._dashboard)
        right_layout.addWidget(dash_wrap)

        right_layout.addWidget(self._make_section_header("// OPTIONS"))
        opts_wrap = QWidget()
        opts_wrap.setStyleSheet("background: transparent;")
        ow = QVBoxLayout(opts_wrap)
        ow.setContentsMargins(16, 12, 16, 12)
        ow.setSpacing(10)

        self._modifier_toggle = QCheckBox("  APPLY MODIFIER FILES")
        self._modifier_toggle.setFont(QFont("Courier New", 11))
        self._modifier_toggle.setStyleSheet(
            f"color: {_W}; background: transparent; spacing: 8px;"
        )
        self._modifier_toggle.setChecked(True)

        self._verbose_toggle = QCheckBox("  VERBOSE LOGGING")
        self._verbose_toggle.setFont(QFont("Courier New", 11))
        self._verbose_toggle.setStyleSheet(
            f"color: {_W}; background: transparent; spacing: 8px;"
        )

        ow.addWidget(self._modifier_toggle)
        ow.addWidget(self._verbose_toggle)
        right_layout.addWidget(opts_wrap)

        right_layout.addStretch(1)

        footer = QWidget()
        footer.setStyleSheet(
            f"background: {THEME['surface']}; "
            f"border-top: 1px solid {THEME['border']};"
        )
        fw = QVBoxLayout(footer)
        fw.setContentsMargins(16, 10, 16, 10)
        info = QLabel("PYTHON 3.13 · PYQT6 · PANDAS 2.2")
        info.setFont(QFont("Courier New", 9))
        info.setStyleSheet(f"color: {_M}; background: transparent;")
        fw.addWidget(info)
        right_layout.addWidget(footer)

        root.addWidget(right, 2)

    # _make_nav_cell: Single QWidget cell with vertically centred labels inside.
    def _make_nav_cell(self, icon: str, name: str, desc: str,
                       callback, primary: bool = False) -> QWidget:
        cell = QWidget()
        cell.setCursor(Qt.CursorShape.PointingHandCursor)
        cell.setObjectName("navCell")

        # Primary cell gets green border at rest; all others get dark border
        border = _G if primary else "#2a2a2a"
        cell.setStyleSheet(f"""
            QWidget#navCell {{
                background-color: {THEME['surface']};
                border: 1px solid {border};
            }}
            QWidget#navCell:hover {{
                background-color: #0d1a0d;
                border-color: {_G};
            }}
        """)
        cell.mousePressEvent = lambda _e: callback()

        vbox = QVBoxLayout(cell)
        vbox.setContentsMargins(28, 0, 28, 0)
        vbox.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Courier New", 14))
        icon_lbl.setStyleSheet(
            f"color: {_G if primary else _M}; background: transparent; border: none;"
        )

        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Courier New", 16, QFont.Weight.Bold))
        name_lbl.setStyleSheet(
            f"color: {_W}; background: transparent; border: none; letter-spacing: 1px;"
        )

        desc_lbl = QLabel(desc)
        desc_lbl.setFont(QFont("Courier New", 10))
        desc_lbl.setStyleSheet(
            f"color: {_M}; background: transparent; border: none;"
        )

        vbox.addWidget(icon_lbl)
        vbox.addWidget(name_lbl)
        vbox.addWidget(desc_lbl)
        return cell

    # _make_section_header: Green label bar for right-column section separators.
    def _make_section_header(self, text: str) -> QWidget:
        wrap = QWidget()
        wrap.setFixedHeight(32)
        wrap.setStyleSheet(
            f"background: {THEME['bg']}; "
            f"border-bottom: 1px solid {THEME['border']};"
        )
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(16, 0, 16, 0)
        lbl = QLabel(text)
        lbl.setFont(QFont("Courier New", 10))
        lbl.setStyleSheet(f"color: {_G}; background: transparent; letter-spacing: 2px;")
        layout.addWidget(lbl)
        return wrap

    def on_enter(self):
        self._refresh_status()

    # _refresh_status: Pull live state and update all three status indicators.
    def _refresh_status(self):
        batch_ok    = self._ctrl.is_batch_ready()
        modifier_ok = self._ctrl.is_modifier_ready()
        n_trials    = self._ctrl.next_trial_number() - 1

        self._batch_ind.set_ready(
            batch_ok,
            "BATCH FILES READY" if batch_ok else "NO BATCH LOADED"
        )
        self._modifier_ind.set_ready(
            modifier_ok,
            "MODIFIER DATA LOADED" if modifier_ok else "MODIFIER MISSING"
        )
        self._trials_ind.set_ready(
            n_trials > 0,
            f"{n_trials} TRIAL(S) ON DISK" if n_trials > 0 else "NO TRIALS RUN YET"
        )
        self._dashboard.refresh(self._ctrl)

    # _go_to_game_world: Auto-load the SF feed if needed, then navigate.
    def _go_to_game_world(self):
        if not self._ctrl.is_batch_ready():
            gtfs_dir = os.path.join(
                self._ctrl.gtfs_root, "San Francisco (muni_gtfs-current)"
            )
            if os.path.isdir(gtfs_dir):
                self._ctrl.load_city_feed("San Francisco", gtfs_dir)
        self._ctrl.screen_manager.navigate(ScreenManager.GAME_WORLD)

    # modifier_enabled: Whether the user wants modifier data applied to the simulation.
    def modifier_enabled(self) -> bool:
        return self._modifier_toggle.isChecked()
