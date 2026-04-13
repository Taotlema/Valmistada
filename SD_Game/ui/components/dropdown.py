# dropdown: Accordion row and file entry for the Input and Output screens.

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame)
from PyQt6.QtCore    import Qt, pyqtSignal
from ui.base.base_widget  import THEME
from ui.components.button import SecondaryButton

_G = THEME["primary"]
_T = THEME["text"]
_M = THEME["muted"]


# DropdownRow: Expandable accordion row with a green left-accent when open.
class DropdownRow(QWidget):

    toggled = pyqtSignal(bool)

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._open = False
        self._build(title)

    def _build(self, title: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 1)
        root.setSpacing(0)

        self._header = QFrame()
        self._header.setFixedHeight(42)
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['surface']};
                border: 1px solid #2a2a2a;
                border-left: 3px solid #2a2a2a;
            }}
            QFrame:hover {{ border-left-color: {_G}; }}
        """)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.mousePressEvent = lambda _e: self.toggle()

        hbox = QHBoxLayout(self._header)
        hbox.setContentsMargins(14, 0, 14, 0)

        self._arrow = QLabel("▶")
        self._arrow.setStyleSheet(
            f"color: {_M}; font-size: 10px; font-family: {THEME['font']};"
        )
        self._arrow.setFixedWidth(16)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(
            f"color: {_T}; font-size: 12px; font-weight: bold;"
            f"font-family: {THEME['font']}; letter-spacing: 1px;"
        )

        hbox.addWidget(self._arrow)
        hbox.addWidget(self._title_label, 1)
        root.addWidget(self._header)

        # Content area shown only when the row is open
        self._content = QFrame()
        self._content.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['surface2']};
                border: 1px solid #2a2a2a;
                border-top: none;
                border-left: 3px solid {_G};
            }}
        """)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(18, 10, 18, 10)
        self._content_layout.setSpacing(4)
        self._content.setVisible(False)
        root.addWidget(self._content)

    # toggle: Flip between open and closed states.
    def toggle(self):
        self._open = not self._open
        self._content.setVisible(self._open)
        self._arrow.setText("▼" if self._open else "▶")
        if self._open:
            self._header.setStyleSheet(f"""
                QFrame {{
                    background-color: {THEME['surface2']};
                    border: 1px solid #2a2a2a;
                    border-left: 3px solid {_G};
                }}
            """)
        else:
            self._header.setStyleSheet(f"""
                QFrame {{
                    background-color: {THEME['surface']};
                    border: 1px solid #2a2a2a;
                    border-left: 3px solid #2a2a2a;
                }}
                QFrame:hover {{ border-left-color: {_G}; }}
            """)
        self.toggled.emit(self._open)

    # add_item: Place a widget inside the expanded content area.
    def add_item(self, widget: QWidget):
        self._content_layout.addWidget(widget)

    # clear_items: Remove all content widgets.
    def clear_items(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # set_title: Update the header label text.
    def set_title(self, text: str):
        self._title_label.setText(text)


# FileRow: One file entry with a filename label and optional action button.
class FileRow(QWidget):

    action_clicked = pyqtSignal(str)

    def __init__(self, filename: str, action_label: str = None, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.setStyleSheet("background: transparent;")

        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 2, 0, 2)

        prefix = QLabel(">")
        prefix.setFixedWidth(14)
        prefix.setStyleSheet(
            f"color: {_M}; font-size: 11px; font-family: {THEME['font']};"
        )

        lbl = QLabel(filename)
        lbl.setStyleSheet(f"color: {_T}; font-size: 11px; font-family: {THEME['font']};")

        hbox.addWidget(prefix)
        hbox.addWidget(lbl, 1)

        if action_label:
            btn = SecondaryButton(f"[ {action_label} ]")
            btn.setFixedHeight(24)
            btn.clicked.connect(lambda: self.action_clicked.emit(self.filename))
            hbox.addWidget(btn)
