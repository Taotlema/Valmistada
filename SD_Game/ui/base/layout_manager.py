# layout_manager: Factory helpers for consistent layout construction across all screens.

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy


# LayoutManager: Static helpers to build consistently margined layouts.
class LayoutManager:

    # make_vbox: Vertical box layout with standard app margins.
    @staticmethod
    def make_vbox(parent: QWidget = None,
                  margins: tuple = (16, 16, 16, 16),
                  spacing: int = 10) -> QVBoxLayout:
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout

    # make_hbox: Horizontal box layout with zero margins by default.
    @staticmethod
    def make_hbox(parent: QWidget = None,
                  margins: tuple = (0, 0, 0, 0),
                  spacing: int = 8) -> QHBoxLayout:
        layout = QHBoxLayout(parent)
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout

    # expand: Allow a widget to grow in both directions.
    @staticmethod
    def expand(widget: QWidget):
        widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    # fixed_height: Pin a widget to an exact pixel height.
    @staticmethod
    def fixed_height(widget: QWidget, h: int):
        widget.setFixedHeight(h)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
