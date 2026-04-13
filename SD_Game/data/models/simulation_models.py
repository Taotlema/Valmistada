# simulation_models: Runtime state snapshots used by the simulation engine each tick.

from dataclasses import dataclass, field
from typing import List
import datetime


# SimDate: Lightweight calendar wrapper for one simulation tick.
@dataclass
class SimDate:
    year:  int
    month: int
    day:   int

    # day_type: Derive "Weekday" / "Saturday" / "Sunday" from the calendar date.
    def day_type(self) -> str:
        wd = datetime.date(self.year, self.month, self.day).weekday()
        if wd == 5: return "Saturday"
        if wd == 6: return "Sunday"
        return "Weekday"

    # to_label: Return a human-readable date string.
    def to_label(self) -> str:
        return datetime.date(self.year, self.month, self.day).strftime("%B %d, %Y")

    # to_month_label: Return a "January 2019" style string.
    def to_month_label(self) -> str:
        return datetime.date(self.year, self.month, self.day).strftime("%B %Y")


# VehicleState: Position and status snapshot for one simulated vehicle.
@dataclass
class VehicleState:
    vehicle_id:       str
    route_id:         str
    current_stop_idx: int
    progress:         float   # 0.0 to 1.0 between stops
    passengers:       int  = 0
    active:           bool = True


# RouteState: Daily stats accumulated for one route.
@dataclass
class RouteState:
    route_id:         str
    route_short_name: str
    service_category: str
    daily_boardings:  int = 0
    total_trips:      int = 0


# SimSnapshot: Full simulation state at one tick, used for UI refresh.
@dataclass
class SimSnapshot:
    sim_date:     SimDate
    tick:         int
    vehicles:     List[VehicleState] = field(default_factory=list)
    route_states: List[RouteState]   = field(default_factory=list)
    running:      bool = False
    speed_level:  int  = 1
