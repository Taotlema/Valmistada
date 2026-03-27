"""
Filename: vehicle.py
Author: Ayemhenre Isikhuemhen
Description: Vehicle entity — a worm-like transit unit that crawls along a route's
             stop sequence, boarding and alighting passengers each tick.
Last Updated: March, 2026
"""

# Libraries
import random
from typing import List, TYPE_CHECKING

# Modules
from game_world.entities.base_entity import BaseEntity

if TYPE_CHECKING:
    from game_world.entities.route import RouteEntity
    from game_world.entities.station import Station


# Vehicle: Moves between stations and records boardings for the parent route
class Vehicle(BaseEntity):

    # __init__ (vehicle_id, route, capacity, speed_factor)
    def __init__(self, vehicle_id: str, route: "RouteEntity",
                 capacity: int = 60, speed_factor: float = 1.0):
        super().__init__(entity_id=vehicle_id)
        self.route        = route
        self.capacity     = capacity
        self.speed_factor = speed_factor
        self.passengers   = 0

        self._stop_idx    = 0
        self._progress    = 0.0
        self._dwell_ticks = 0

        self.x_px: float  = 0.0
        self.y_px: float  = 0.0

    # update (tick, dt): Advance position or dwell; board/alight at stations
    def update(self, tick: int, dt: float):
        if not self.active or len(self.route.stations) < 2:
            return

        if self._dwell_ticks > 0:
            self._dwell_ticks -= 1
            return

        advance = (self.speed_factor * dt) / self._segment_duration()
        self._progress += advance

        if self._progress >= 1.0:
            self._progress = 0.0
            self._arrive_at_next_stop()

    # _segment_duration: Ticks to traverse one inter-stop segment
    def _segment_duration(self) -> float:
        return max(2.0, 4.0 / self.speed_factor)

    # _arrive_at_next_stop: Board/alight and advance stop index
    def _arrive_at_next_stop(self):
        stations = self.route.stations
        next_idx = (self._stop_idx + 1) % len(stations)
        station  = stations[next_idx]

        alighting = max(0, int(self.passengers * random.uniform(0.2, 0.5)))
        self.passengers -= alighting

        space   = self.capacity - self.passengers
        boarded = station.board(space)
        self.passengers += boarded
        self.route.record_boarding(boarded)

        self._stop_idx    = next_idx
        self._dwell_ticks = 2

    # current_station: The station this vehicle just left
    @property
    def current_station(self) -> "Station":
        return self.route.stations[self._stop_idx]

    # next_station: The station this vehicle is heading toward
    @property
    def next_station(self) -> "Station":
        stations = self.route.stations
        return stations[(self._stop_idx + 1) % len(stations)]

    # progress: Interpolation value for drawing the vehicle between stops
    @property
    def progress(self) -> float:
        return self._progress