"""
Filename: layout_manager.py
Author: Ayemhenre Isikhuemhen
Description: Manages screen layout and navigation for the application.
Last Updated: March, 2026
"""

# Libraries
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy


# LayoutManager: Factory helpers for consistent layout construction
class LayoutManager:

    # make_vbox (parent, margins, spacing): Vertical box layout with app defaults
    @staticmethod
    def make_vbox(parent: QWidget = None, margins: tuple = (16, 16, 16, 16),
                  spacing: int = 10) -> QVBoxLayout:
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout

    # make_hbox (parent, margins, spacing): Horizontal box layout
    @staticmethod
    def make_hbox(parent: QWidget = None, margins: tuple = (0, 0, 0, 0),
                  spacing: int = 8) -> QHBoxLayout:
        layout = QHBoxLayout(parent)
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout

    # expand (widget): Set widget to expand in both directions
    @staticmethod
    def expand(widget: QWidget):
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # fixed_height (widget, h): Pin widget to an exact height
    @staticmethod
    def fixed_height(widget: QWidget, h: int):
        widget.setFixedHeight(h)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)