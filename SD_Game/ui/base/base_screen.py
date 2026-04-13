# base_screen: Abstract base class for all six application screens.

from abc import abstractmethod
from PyQt6.QtWidgets import QWidget

from ui.base.base_widget import THEME
from app_controller.event_bus import EventBus


# BaseScreen: Provides on_enter / on_exit hooks and the dark terminal background.
class BaseScreen(QWidget):

    def __init__(self, bus: EventBus, settings: dict):
        super().__init__()
        self.bus      = bus
        self.settings = settings
        self.theme    = THEME
        self._build()
        self._apply_screen_style()

    # _build: Subclasses construct all their widgets inside this method.
    @abstractmethod
    def _build(self):
        pass

    # on_enter: Called just before this screen becomes visible.
    def on_enter(self):
        pass

    # on_exit: Called just before navigating away from this screen.
    def on_exit(self):
        pass

    # _apply_screen_style: Set the full-window background and font.
    def _apply_screen_style(self):
        self.setStyleSheet(
            f"background-color: {THEME['bg']}; color: {THEME['text']};"
            f"font-family: {THEME['font']};"
        )
