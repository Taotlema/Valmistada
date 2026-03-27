"""
Filename: scroll_area.py
Author: Ayemhenre Isikhuemhen
Description: Themed QScrollArea wrapper used wherever content may overflow vertical space.
Last Updated: March, 2026
"""

# Libraries
from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

# Modules
from ui.base.base_widget import THEME


# AppScrollArea: Styled vertical scroll container with a transparent background
class AppScrollArea(QScrollArea):

    # __init__ (parent)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._apply_style()

        self._inner = QWidget()
        self._inner.setStyleSheet(f"background-color: {THEME['bg']};")
        self._layout = QVBoxLayout(self._inner)
        self._layout.setContentsMargins(0, 0, 8, 0)
        self._layout.setSpacing(6)
        self._layout.addStretch(1)
        self.setWidget(self._inner)

    # _apply_style: Scrollbar chrome and area background
    def _apply_style(self):
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {THEME['bg']};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {THEME['surface']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME['border']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {THEME['accent']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    # add_widget (widget): Append a widget before the trailing stretch
    def add_widget(self, widget: QWidget):
        self._layout.insertWidget(self._layout.count() - 1, widget)

    # clear: Remove all widgets from the inner layout (except the stretch)
    def clear(self):
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()