"""
Filename: base_screen.py
Author: Ayemhenre Isikhuemhen
Description: Abstract base class for all six application screens.
Last Updated: March, 2026
"""

# Libraries
from abc import abstractmethod
from PyQt6.QtWidgets import QWidget

# Modules
from ui.base.base_widget import THEME
from app_controller.event_bus import EventBus


# BaseScreen: Every screen inherits this to get on_enter / on_exit hooks
class BaseScreen(QWidget):

    # __init__ (bus, settings)
    def __init__(self, bus: EventBus, settings: dict):
        super().__init__()
        self.bus      = bus
        self.settings = settings
        self.theme    = THEME
        self._build()
        self._apply_screen_style()

    # _build: Subclasses construct their widgets here — called once in __init__
    @abstractmethod
    def _build(self):
        pass

    # on_enter: Called just before this screen becomes visible
    def on_enter(self):
        pass

    # on_exit: Called just before navigating away
    def on_exit(self):
        pass

    # _apply_screen_style: Full-window background colour
    def _apply_screen_style(self):
        self.setStyleSheet(
            f"background-color: {THEME['bg']}; color: {THEME['text']}; "
            f"font-family: 'Segoe UI', 'Arial', sans-serif;"
        )