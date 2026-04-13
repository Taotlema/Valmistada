# button: Retro terminal push-buttons; dark border at rest, green fill on hover.

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore    import Qt

from ui.base.base_widget import THEME

_MONO = "'Courier New', monospace"

# Shared base stylesheet; colour values filled in by each subclass
_BASE = """
    QPushButton {{
        border: 1px solid #444;
        background-color: {bg};
        color: #cccccc;
        font-family: 'Courier New', monospace;
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 1px;
        padding: 5px 14px;
        border-radius: 0px;
    }}
    QPushButton:hover   {{ background-color: {hover}; color: {htxt}; border-color: {hover}; }}
    QPushButton:pressed {{ background-color: {pressed}; color: {htxt}; }}
    QPushButton:disabled {{ border-color: #222; color: #333; background-color: {bg}; }}
"""


# AppButton: Base push-button; dark border at rest, phosphor green on hover.
class AppButton(QPushButton):

    def __init__(self, label: str, parent=None):
        super().__init__(label, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply()

    # _apply: Override in subclasses to choose a different colour set.
    def _apply(self):
        self.setStyleSheet(_BASE.format(
            bg=THEME["bg"],
            hover=THEME["primary"], htxt="#000000",
            pressed="#00cc66",
        ))


# PrimaryButton: Same styling as AppButton; used for main call-to-action buttons.
class PrimaryButton(AppButton):
    def _apply(self):
        self.setStyleSheet(_BASE.format(
            bg=THEME["bg"],
            hover=THEME["primary"], htxt="#000000",
            pressed="#00cc66",
        ))


# SecondaryButton: Same as primary; used for navigation and back buttons.
class SecondaryButton(AppButton):
    def _apply(self):
        self.setStyleSheet(_BASE.format(
            bg=THEME["bg"],
            hover=THEME["primary"], htxt="#000000",
            pressed="#00cc66",
        ))


# DangerButton: Red text at rest, red fill on hover; used for destructive actions.
class DangerButton(AppButton):
    def _apply(self):
        self.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid #555;
                background-color: {THEME['bg']};
                color: #ff4444;
                font-family: {_MONO};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 5px 14px;
                border-radius: 0px;
            }}
            QPushButton:hover   {{ background-color: #ff4444; color: #fff; border-color: #ff4444; }}
            QPushButton:pressed {{ background-color: #cc0000; color: #fff; border-color: #cc0000; }}
            QPushButton:disabled {{ border-color: #222; color: #333; }}
        """)


# IconButton: Compact square button for the speed selector and toolbars.
class IconButton(AppButton):

    def __init__(self, label: str, size: int = 36, parent=None):
        super().__init__(label, parent)
        self.setFixedSize(size, size)

    def _apply(self):
        self.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid #333;
                background-color: {THEME['bg']};
                color: #888;
                font-family: {_MONO};
                font-size: 10px;
                font-weight: bold;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                border-color: {THEME['primary']};
                color: {THEME['primary']};
                background-color: {THEME['bg']};
            }}
            QPushButton:pressed {{ background-color: {THEME['surface']}; }}
        """)
