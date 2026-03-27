"""
Filename: base_widget.py
Author: Ayemhenre Isikhuemhen
Description: Base class for all reusable UI widgets — defines the shared colour theme.
Last Updated: March, 2026
"""

# Libraries
from PyQt6.QtWidgets import QWidget


# THEME: Central colour palette used across all widgets and screens
THEME = {
    "bg":      "#1A1A2E",
    "surface": "#16213E",
    "primary": "#1565C0",
    "accent":  "#42A5F5",
    "text":    "#E0E0E0",
    "muted":   "#78909C",
    "success": "#66BB6A",
    "danger":  "#EF5350",
    "border":  "#0F3460",
}


# BaseWidget: All custom widgets inherit from here for consistent theming
class BaseWidget(QWidget):

    # __init__ (parent)
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.theme = THEME
        self.apply_style()

    # apply_style: Override in subclasses for widget-specific stylesheets
    def apply_style(self):
        self.setStyleSheet(
            f"background-color: {THEME['surface']}; color: {THEME['text']};"
        )