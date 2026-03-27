"""
Filename: status_indicator.py
Author: Ayemhenre Isikhuemhen
Description: Circular status dot with an adjacent label — used for batch-ready
             and modifier-ready signals on the Start screen and sim panel.
Last Updated: March, 2026
"""

# Libraries
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QRectF

# Modules
from ui.base.base_widget import THEME


# StatusDot: Painted circle whose colour reflects a boolean ready-state
class StatusDot(QWidget):

    DOT_SIZE = 14

    # __init__ (ready: initial state, parent)
    def __init__(self, ready: bool = False, parent=None):
        super().__init__(parent)
        self._ready = ready
        self.setFixedSize(self.DOT_SIZE, self.DOT_SIZE)

    # set_ready (state): Toggle between green (ready) and red (not ready)
    def set_ready(self, state: bool):
        self._ready = state
        self.update()

    # paintEvent: Draw the filled circle
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(THEME["success"]) if self._ready else QColor(THEME["danger"])
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(0, 0, self.DOT_SIZE, self.DOT_SIZE))


# StatusIndicator: StatusDot + descriptive label side by side
class StatusIndicator(QWidget):

    # __init__ (label_text, ready, parent)
    def __init__(self, label_text: str, ready: bool = False, parent=None):
        super().__init__(parent)
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(8)

        self._dot   = StatusDot(ready)
        self._label = QLabel(label_text)
        self._label.setStyleSheet(f"color: {THEME['muted']}; font-size: 12px;")

        hbox.addWidget(self._dot)
        hbox.addWidget(self._label)
        hbox.addStretch()

    # set_ready (state, label_text): Update dot colour and optionally the label
    def set_ready(self, state: bool, label_text: str = None):
        self._dot.set_ready(state)
        if label_text:
            self._label.setText(label_text)