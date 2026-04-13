# vehicle: A worm-like transit unit that crawls along a route's stop sequence.

import random
from typing import TYPE_CHECKING
from game_world.entities.base_entity import BaseEntity

if TYPE_CHECKING:
    from game_world.entities.route   import RouteEntity
    from game_world.entities.station import Station


# Vehicle: Moves between stations, boarding and alighting passengers at each stop.
class Vehicle(BaseEntity):

    def __init__(self, vehicle_id: str, route: "RouteEntity",
                 capacity: int = 60, speed_factor: float = 1.0):
        super().__init__(entity_id=vehicle_id)
        self.route        = route
        self.capacity     = capacity
        self.speed_factor = speed_factor
        self.passengers   = 0
        self._stop_idx    = 0      # index of the last station visited
        self._progress    = 0.0    # 0.0 to 1.0 between current and next stop
        self._dwell_ticks = 0      # ticks remaining at a station
        self.x_px: float  = 0.0   # pixel position set by RendererAdapter
        self.y_px: float  = 0.0

    # update: Advance position one tick; handle dwell time and stop arrival.
    def update(self, tick: int, dt: float):
        if not self.active or len(self.route.stations) < 2:
            return
        if self._dwell_ticks > 0:
            self._dwell_ticks -= 1
            return
        self._progress += (self.speed_factor * dt) / self._segment_duration()
        if self._progress >= 1.0:
            self._progress = 0.0
            self._arrive_at_next_stop()

    # _segment_duration: Ticks to traverse one inter-stop segment at current speed.
    def _segment_duration(self) -> float:
        return max(2.0, 4.0 / self.speed_factor)

    # _arrive_at_next_stop: Alight a random fraction of passengers, board waiting ones.
    def _arrive_at_next_stop(self):
        stations = self.route.stations
        next_idx = (self._stop_idx + 1) % len(stations)
        station  = stations[next_idx]

        # Random fraction alights at each stop to simulate destination variation
        alighting       = max(0, int(self.passengers * random.uniform(0.2, 0.5)))
        self.passengers -= alighting

        boarded          = station.board(self.capacity - self.passengers)
        self.passengers += boarded
        self.route.record_boarding(boarded)

        self._stop_idx    = next_idx
        self._dwell_ticks = 2   # brief pause at each station

    @property
    def current_station(self) -> "Station":
        return self.route.stations[self._stop_idx]

    @property
    def next_station(self) -> "Station":
        return self.route.stations[(self._stop_idx + 1) % len(self.route.stations)]

    @property
    def progress(self) -> float:
        return self._progress
