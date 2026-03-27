"""
Filename: simulation_models.py
Author: Ayemhenre Isikhuemhen
Description: Runtime state models used by the simulation engine each tick.
Last Updated: March, 2026
"""

# Libraries
from dataclasses import dataclass, field
from typing import List, Optional
import datetime


# SimDate: Lightweight calendar wrapper for one sim tick
@dataclass
class SimDate:
    year: int
    month: int
    day: int

    # day_type: Derive Weekday / Saturday / Sunday label
    def day_type(self) -> str:
        wd = datetime.date(self.year, self.month, self.day).weekday()
        if wd == 5:
            return "Saturday"
        if wd == 6:
            return "Sunday"
        return "Weekday"

    def to_label(self) -> str:
        return datetime.date(self.year, self.month, self.day).strftime("%B %d, %Y")

    def to_month_label(self) -> str:
        return datetime.date(self.year, self.month, self.day).strftime("%B %Y")


# VehicleState: Position and status of one simulated vehicle
@dataclass
class VehicleState:
    vehicle_id: str
    route_id: str
    current_stop_idx: int
    progress: float             # 0.0–1.0 between current and next stop
    passengers: int = 0
    active: bool = True


# RouteState: Aggregated daily stats accumulated for one route
@dataclass
class RouteState:
    route_id: str
    route_short_name: str
    service_category: str
    daily_boardings: int = 0
    total_trips: int = 0


# SimSnapshot: State of the whole simulation at a given tick
@dataclass
class SimSnapshot:
    sim_date: SimDate
    tick: int
    vehicles: List[VehicleState] = field(default_factory=list)
    route_states: List[RouteState] = field(default_factory=list)
    running: bool = False
    speed_level: int = 1