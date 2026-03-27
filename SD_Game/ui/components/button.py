"""
Filename: button.py
Author: Ayemhenre Isikhuemhen
Description: Reusable styled push-button with primary, secondary, and danger variants.
Last Updated: March, 2026
"""

# Libraries
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt

# Modules
from ui.base.base_widget import THEME


# AppButton: Themed push-button base — subclasses pick a visual variant
class AppButton(QPushButton):

    _BASE = """
        QPushButton {{
            border-radius: 6px;
            padding: 8px 18px;
            font-size: 13px;
            font-weight: 600;
            border: none;
            color: {text};
            background-color: {bg};
        }}
        QPushButton:hover   {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {pressed}; }}
        QPushButton:disabled {{ background-color: {disabled}; color: #607D8B; }}
    """

    # __init__ (label, parent)
    def __init__(self, label: str, parent=None):
        super().__init__(label, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply()

    # _apply: Override in subclasses to choose colour set
    def _apply(self):
        self.setStyleSheet(self._BASE.format(
            text=THEME["text"], bg=THEME["primary"],
            hover="#1976D2", pressed="#0D47A1", disabled="#37474F"
        ))


# PrimaryButton: Main call-to-action — blue fill
class PrimaryButton(AppButton):
    def _apply(self):
        self.setStyleSheet(self._BASE.format(
            text="#FFFFFF", bg=THEME["primary"],
            hover="#1976D2", pressed="#0D47A1", disabled="#37474F"
        ))


# SecondaryButton: Subdued bordered style for navigation actions
class SecondaryButton(AppButton):
    def _apply(self):
        self.setStyleSheet(f"""
            QPushButton {{
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 600;
                border: 1px solid {THEME['border']};
                color: {THEME['accent']};
                background-color: transparent;
            }}
            QPushButton:hover   {{ background-color: {THEME['border']}; }}
            QPushButton:pressed {{ background-color: #0A2744; }}
            QPushButton:disabled {{ color: #607D8B; border-color: #37474F; }}
        """)


# DangerButton: Red tone for destructive / abort actions
class DangerButton(AppButton):
    def _apply(self):
        self.setStyleSheet(self._BASE.format(
            text="#FFFFFF", bg=THEME["danger"],
            hover="#E53935", pressed="#B71C1C", disabled="#37474F"
        ))


# IconButton: Compact square button for toolbar-style icon actions
class IconButton(AppButton):
    # __init__ (label, size: pixel side length)
    def __init__(self, label: str, size: int = 36, parent=None):
        super().__init__(label, parent)
        self.setFixedSize(size, size)

    def _apply(self):
        self.setStyleSheet(f"""
            QPushButton {{
                border-radius: 4px;
                font-size: 12px;
                font-weight: 700;
                border: 1px solid {THEME['border']};
                color: {THEME['text']};
                background-color: {THEME['surface']};
            }}
            QPushButton:hover   {{ background-color: {THEME['border']}; }}
            QPushButton:pressed {{ background-color: #0A2744; }}
        """)