# base_widget: Base widget class and shared retro-terminal colour theme.

from PyQt6.QtWidgets import QWidget

# THEME: Phosphor-green terminal palette used across every screen and component.
THEME = {
    "bg":        "#0a0a0a",
    "surface":   "#111111",
    "surface2":  "#161616",
    "primary":   "#00ff88",
    "accent":    "#00ff88",
    "text":      "#cccccc",
    "muted":     "#555555",
    "success":   "#00ff88",
    "danger":    "#ff4444",
    "warning":   "#ffaa00",
    "border":    "#2a2a2a",
    "border_hi": "#00ff88",
    "font":      "'Courier New', 'Courier', monospace",
}


# BaseWidget: Root QWidget subclass that exposes the THEME dict to components.
class BaseWidget(QWidget):

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.theme = THEME
        self.apply_style()

    # apply_style: Override in subclasses to apply component-specific stylesheets.
    def apply_style(self):
        self.setStyleSheet(
            f"background-color: {THEME['surface']}; color: {THEME['text']};"
            f"font-family: {THEME['font']};"
        )
