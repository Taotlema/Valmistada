# dashboard_widget: Retro stat cards for the start screen sidebar.

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QFont

from ui.base.base_widget import THEME


# StatCard: Single metric tile with a green top accent, large value, and bold label.
class StatCard(QWidget):

    def __init__(self, title: str, value: str = "0", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            background-color: {THEME['surface']};
            border: 1px solid {THEME['border']};
            border-top: 2px solid {THEME['accent']};
        """)
        self.setMinimumWidth(100)
        self.setMinimumHeight(80)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(14, 14, 14, 10)
        vbox.setSpacing(8)

        # Large green number displayed prominently
        self._value = QLabel(value)
        self._value.setFont(QFont("Courier New", 26, QFont.Weight.Bold))
        self._value.setStyleSheet(f"color: {THEME['accent']}; background: transparent;")
        self._value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        # Bold white category label below the number
        self._title = QLabel(title.upper())
        self._title.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self._title.setStyleSheet(
            "color: #ffffff; background: transparent; letter-spacing: 2px;"
        )
        self._title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        vbox.addWidget(self._value)
        vbox.addSpacing(4)
        vbox.addWidget(self._title)

    # set_value: Update the displayed metric text.
    def set_value(self, text: str):
        self._value.setText(text)


# DashboardWidget: 2x2 grid of StatCards showing live session statistics.
class DashboardWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(12, 12, 12, 12)
        wrapper.setSpacing(0)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(1)

        self.card_cities   = StatCard("CITIES",   "01")
        self.card_routes   = StatCard("ROUTES",   "68")
        self.card_trials   = StatCard("TRIALS",   "00")
        self.card_modifier = StatCard("MODIFIER", "OK")

        grid.addWidget(self.card_cities,   0, 0)
        grid.addWidget(self.card_routes,   0, 1)
        grid.addWidget(self.card_trials,   1, 0)
        grid.addWidget(self.card_modifier, 1, 1)

        wrapper.addLayout(grid)

    # refresh: Pull live counts from AppController and update all four cards.
    def refresh(self, app_controller):
        n_cities = len(app_controller.feeds)
        n_routes = sum(len(f.routes) for f in app_controller.feeds.values())
        n_trials = app_controller.next_trial_number() - 1
        mod_ok   = app_controller.is_modifier_ready()

        self.card_cities.set_value(str(n_cities))
        self.card_routes.set_value(str(n_routes) if n_routes else "-")
        self.card_trials.set_value(str(n_trials))
        self.card_modifier.set_value("OK" if mod_ok else "NO")
