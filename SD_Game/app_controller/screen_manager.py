# screen_manager: Named screen navigation over QStackedWidget with on_enter/on_exit hooks.

from PyQt6.QtWidgets import QStackedWidget
import logging

from app_controller.event_bus import EventBus, Events

log = logging.getLogger(__name__)


# ScreenManager: Manages six application screens by name and fires lifecycle hooks.
class ScreenManager(QStackedWidget):

    # Screen name constants
    LOADING    = "loading"
    START      = "start"
    INPUT      = "input"
    OUTPUT     = "output"
    DICTIONARY = "dictionary"
    GAME_WORLD = "game_world"

    def __init__(self, bus: EventBus):
        super().__init__()
        self.bus = bus
        self._screens: dict = {}

    # register: Map a name string to a screen widget and add it to the stack.
    def register(self, name: str, widget):
        self._screens[name] = widget
        self.addWidget(widget)

    # navigate: Switch to a named screen; fires on_exit then on_enter hooks.
    def navigate(self, name: str):
        if name not in self._screens:
            log.warning(f"Unknown screen: {name}")
            return

        current = self.currentWidget()
        if current and hasattr(current, "on_exit"):
            try:
                current.on_exit()
            except Exception as e:
                log.error(f"on_exit error: {e}")

        self.setCurrentWidget(self._screens[name])
        self.bus.publish(Events.SCREEN_CHANGE, name)

        incoming = self._screens[name]
        if hasattr(incoming, "on_enter"):
            try:
                incoming.on_enter()
            except Exception as e:
                log.error(f"on_enter error: {e}")

        log.info(f"Navigated to {name}")

    # current_name: Return the name key of the currently visible screen.
    def current_name(self) -> str:
        widget = self.currentWidget()
        for name, w in self._screens.items():
            if w is widget:
                return name
        return ""
