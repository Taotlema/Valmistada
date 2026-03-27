"""
Filename: screen_manager.py
Author: Ayemhenre Isikhuemhen
Description: Manages screen lifecycle and navigation using a QStackedWidget.
Last Updated: March, 2026
"""

# Libraries
from PyQt6.QtWidgets import QStackedWidget
import logging

# Modules
from app_controller.event_bus import EventBus, Events

log = logging.getLogger(__name__)


# ScreenManager: Wraps QStackedWidget to provide named screen navigation
class ScreenManager(QStackedWidget):

    # Screen name constants
    LOADING     = "loading"
    START       = "start"
    INPUT       = "input"
    OUTPUT      = "output"
    DICTIONARY  = "dictionary"
    GAME_WORLD  = "game_world"

    # __init__ (bus: shared EventBus)
    def __init__(self, bus: EventBus):
        super().__init__()
        self.bus = bus
        self._screens: dict = {}

    # register (name, widget): Add a screen widget and map it to a string key
    def register(self, name: str, widget):
        self._screens[name] = widget
        self.addWidget(widget)
        log.debug(f"Screen registered: {name}")

    # navigate (name): Switch the visible screen; publishes SCREEN_CHANGE event
    def navigate(self, name: str):
        if name not in self._screens:
            log.warning(f"Unknown screen: {name}")
            return
        self.setCurrentWidget(self._screens[name])
        self.bus.publish(Events.SCREEN_CHANGE, name)
        log.info(f"Navigated → {name}")

    # current_name: Return the key of the currently visible screen
    def current_name(self) -> str:
        widget = self.currentWidget()
        for name, w in self._screens.items():
            if w is widget:
                return name
        return ""