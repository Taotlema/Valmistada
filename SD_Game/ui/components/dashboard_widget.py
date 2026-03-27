"""
Filename: dashboard_widget.py
Author: Ayemhenre Isikhuemhen
Description: Small stat-card widget displaying a title and a live value —
             used on the Start screen dashboard panel.
Last Updated: March, 2026
"""

# Libraries
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

# Modules
from ui.base.base_widget import THEME


# StatCard: Single metric display with a muted title and prominent value
class StatCard(QWidget):

    # __init__ (title, value, parent)
    def __init__(self, title: str, value: str = "—", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            background-color: {THEME['surface']};
            border: 1px solid {THEME['border']};
            border-radius: 8px;
        """)
        self.setMinimumWidth(140)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(14, 12, 14, 12)
        vbox.setSpacing(4)

        self._title = QLabel(title)
        self._title.setStyleSheet(
            f"color: {THEME['muted']}; font-size: 11px; font-weight: 600;"
        )
        self._title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._value = QLabel(value)
        self._value.setStyleSheet(
            f"color: {THEME['accent']}; font-size: 22px; font-weight: 700;"
        )
        self._value.setAlignment(Qt.AlignmentFlag.AlignLeft)

        vbox.addWidget(self._title)
        vbox.addWidget(self._value)

    # set_value (text): Update the displayed metric
    def set_value(self, text: str):
        self._value.setText(text)


# DashboardWidget: Row of StatCards showing system-level batch status
class DashboardWidget(QWidget):

    # __init__ (parent)
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent;")
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self.card_cities   = StatCard("Cities Loaded", "0")
        self.card_routes   = StatCard("Routes",        "—")
        self.card_trials   = StatCard("Trials Run",    "0")
        self.card_modifier = StatCard("Modifier Data", "—")

        row.addWidget(self.card_cities)
        row.addWidget(self.card_routes)
        row.addWidget(self.card_trials)
        row.addWidget(self.card_modifier)
        row.addStretch()
        root.addWidget(row_widget)

    # refresh (app_controller): Pull live counts from the app state
    def refresh(self, app_controller):
        n_cities = len(app_controller.feeds)
        n_routes = sum(len(f.routes) for f in app_controller.feeds.values())
        n_trials = app_controller.next_trial_number() - 1
        mod_ok   = app_controller.is_modifier_ready()

        self.card_cities.set_value(str(n_cities))
        self.card_routes.set_value(str(n_routes) if n_routes else "—")
        self.card_trials.set_value(str(n_trials))
        self.card_modifier.set_value("Ready" if mod_ok else "Missing")