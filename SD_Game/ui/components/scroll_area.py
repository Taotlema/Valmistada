# scroll_area: Retro-styled vertical scroll area with a thin green scrollbar.

from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout
from PyQt6.QtCore    import Qt

from ui.base.base_widget import THEME


# AppScrollArea: Vertical-only scroll area used on Input, Output, and Dictionary screens.
class AppScrollArea(QScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet(f"""
            QScrollArea {{ background-color: {THEME['bg']}; border: none; }}
            QScrollBar:vertical {{
                background: {THEME['surface']};
                width: 6px;
                border-radius: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME['border']};
                min-height: 20px;
                border-radius: 0px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {THEME['primary']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._inner = QWidget()
        self._inner.setStyleSheet(f"background-color: {THEME['bg']};")
        self._layout = QVBoxLayout(self._inner)
        self._layout.setContentsMargins(0, 0, 6, 0)
        self._layout.setSpacing(1)
        self._layout.addStretch(1)
        self.setWidget(self._inner)

    # add_widget: Insert a widget before the trailing stretch.
    def add_widget(self, widget: QWidget):
        self._layout.insertWidget(self._layout.count() - 1, widget)

    # clear: Remove all content widgets except the trailing stretch.
    def clear(self):
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
