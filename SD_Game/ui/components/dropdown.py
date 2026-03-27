"""
Filename: dropdown.py
Author: Ayemhenre Isikhuemhen
Description: Accordion-style expandable row widget used on the Input and Output screens.
Last Updated: March, 2026
"""

# Libraries
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal

# Modules
from ui.base.base_widget import THEME
from ui.components.button import SecondaryButton


# DropdownRow: A labelled header bar that expands to reveal child widgets
class DropdownRow(QWidget):

    toggled = pyqtSignal(bool)

    # __init__ (title, parent)
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._open = False
        self._build(title)

    # _build (title): Construct the header bar and hidden content area
    def _build(self, title: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 4)
        root.setSpacing(0)

        self._header = QFrame()
        self._header.setFixedHeight(48)
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['surface']};
                border: 1px solid {THEME['border']};
                border-radius: 6px;
            }}
            QFrame:hover {{ border-color: {THEME['accent']}; }}
        """)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.mousePressEvent = lambda _e: self.toggle()

        hbox = QHBoxLayout(self._header)
        hbox.setContentsMargins(14, 0, 14, 0)

        self._arrow = QLabel("▶")
        self._arrow.setStyleSheet(f"color: {THEME['accent']}; font-size: 11px;")
        self._arrow.setFixedWidth(16)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(
            f"color: {THEME['text']}; font-size: 14px; font-weight: 600;"
        )

        hbox.addWidget(self._arrow)
        hbox.addWidget(self._title_label, 1)
        root.addWidget(self._header)

        self._content = QFrame()
        self._content.setStyleSheet(f"""
            QFrame {{
                background-color: #111827;
                border: 1px solid {THEME['border']};
                border-top: none;
                border-radius: 0 0 6px 6px;
            }}
        """)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(18, 8, 18, 8)
        self._content_layout.setSpacing(4)
        self._content.setVisible(False)
        root.addWidget(self._content)

    # toggle: Flip open/closed state
    def toggle(self):
        self._open = not self._open
        self._content.setVisible(self._open)
        self._arrow.setText("▼" if self._open else "▶")
        self.toggled.emit(self._open)

    # add_item (widget): Place a widget inside the expanded content area
    def add_item(self, widget: QWidget):
        self._content_layout.addWidget(widget)

    # clear_items: Remove all content widgets
    def clear_items(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # set_title (text): Update the header label
    def set_title(self, text: str):
        self._title_label.setText(text)


# FileRow: One file entry inside a DropdownRow — label + optional action button
class FileRow(QWidget):

    action_clicked = pyqtSignal(str)

    # __init__ (filename, action_label: button text or None to hide)
    def __init__(self, filename: str, action_label: str = None, parent=None):
        super().__init__(parent)
        self.filename = filename
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 2, 0, 2)

        icon = QLabel("📄")
        icon.setFixedWidth(20)
        icon.setStyleSheet("font-size: 12px;")

        lbl = QLabel(filename)
        lbl.setStyleSheet(f"color: {THEME['muted']}; font-size: 12px;")

        hbox.addWidget(icon)
        hbox.addWidget(lbl, 1)

        if action_label:
            btn = SecondaryButton(action_label)
            btn.setFixedSize(90, 26)
            btn.setStyleSheet(btn.styleSheet() + "padding: 2px 8px; font-size: 11px;")
            btn.clicked.connect(lambda: self.action_clicked.emit(self.filename))
            hbox.addWidget(btn)