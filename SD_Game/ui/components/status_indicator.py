# status_indicator: Square status dot paired with a readable label.

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui     import QPainter, QColor, QBrush
from PyQt6.QtCore    import Qt, QRectF
from ui.base.base_widget import THEME


# StatusDot: Painted square; green when ready, red when not.
class StatusDot(QWidget):

    DOT_SIZE = 12

    def __init__(self, ready: bool = False, parent=None):
        super().__init__(parent)
        self._ready = ready
        self.setFixedSize(self.DOT_SIZE, self.DOT_SIZE)

    # set_ready: Toggle between green and red states.
    def set_ready(self, state: bool):
        self._ready = state
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setBrush(QBrush(QColor(THEME["success"] if self._ready else THEME["danger"])))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(QRectF(0, 0, self.DOT_SIZE, self.DOT_SIZE))


# StatusIndicator: StatusDot paired with a white text label.
class StatusIndicator(QWidget):

    def __init__(self, label_text: str, ready: bool = False, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(14)

        self._dot   = StatusDot(ready)
        self._label = QLabel(label_text)
        self._label.setStyleSheet(
            "color: #e0e0e0; font-size: 13px;"
            f"font-family: {THEME['font']}; letter-spacing: 1px;"
        )
        hbox.addWidget(self._dot)
        hbox.addWidget(self._label)
        hbox.addStretch()

    # set_ready: Update the dot colour and optionally change the label text.
    def set_ready(self, state: bool, label_text: str = None):
        self._dot.set_ready(state)
        if label_text:
            self._label.setText(label_text)
