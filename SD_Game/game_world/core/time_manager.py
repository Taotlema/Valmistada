# time_manager: Advances the simulation calendar tick by tick through a full year.

import datetime
import logging

log = logging.getLogger(__name__)


# TimeManager: Manages the simulated date and fires day/month/year-end callbacks.
class TimeManager:

    def __init__(self, sim_year: int = 2019, ticks_per_day: int = 288):
        self.sim_year      = sim_year
        self.ticks_per_day = ticks_per_day
        self._date         = datetime.date(sim_year, 1, 1)
        self._tick         = 0        # tick within the current day
        self._total_ticks  = 0        # ticks since sim start
        self._total_days   = (
            datetime.date(sim_year + 1, 1, 1) - datetime.date(sim_year, 1, 1)
        ).days
        self._day_number   = 0        # days elapsed since Jan 1

        # Callbacks assigned by SimulationEngine
        self.on_new_day    = None
        self.on_new_month  = None
        self.on_year_end   = None

    # advance: Move forward one tick; fire boundary callbacks at day/month/year edges.
    def advance(self):
        self._tick        += 1
        self._total_ticks += 1

        if self._tick >= self.ticks_per_day:
            self._tick       = 0
            self._day_number += 1
            prev_month        = self._date.month
            self._date       += datetime.timedelta(days=1)

            if self.on_new_day:
                self.on_new_day(self._date)

            if self._date.month != prev_month and self.on_new_month:
                self.on_new_month(self._date)

            if self._date.year != self.sim_year and self.on_year_end:
                self.on_year_end()

    # current_date_label: "January 15, 2019" style display string.
    def current_date_label(self) -> str:
        return self._date.strftime("%B %d, %Y")

    # current_month_label: "January 2019" style string for the aggregator key.
    def current_month_label(self) -> str:
        return self._date.strftime("%B %Y")

    # day_type: "Weekday" / "Saturday" / "Sunday" for the current date.
    def day_type(self) -> str:
        wd = self._date.weekday()
        if wd == 5: return "Saturday"
        if wd == 6: return "Sunday"
        return "Weekday"

    # hour_of_day: Float hour 0.0 to 23.99 derived from the current tick position.
    def hour_of_day(self) -> float:
        return (self._tick / self.ticks_per_day) * 24.0

    # progress: Fraction of the full year completed, clamped to 0.0 to 1.0.
    def progress(self) -> float:
        return min(self._day_number / self._total_days, 1.0)

    # reset: Rewind to January 1 of the simulation year.
    def reset(self):
        self._date        = datetime.date(self.sim_year, 1, 1)
        self._tick        = 0
        self._total_ticks = 0
        self._day_number  = 0
