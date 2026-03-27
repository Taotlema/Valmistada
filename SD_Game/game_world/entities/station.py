"""
Filename: station.py
Author: Ayemhenre Isikhuemhen
Description: Station entity — one GTFS stop on the map with a waiting passenger count.
Last Updated: March, 2026
"""

# Libraries
import random

# Modules
from game_world.entities.base_entity import BaseEntity


# Station: One boarding/alighting node derived from a GTFS stop
class Station(BaseEntity):

    # __init__ (stop_id, name, lat, lon, base_demand)
    def __init__(self, stop_id: str, name: str, lat: float, lon: float,
                 base_demand: float = 100.0):
        super().__init__(entity_id=stop_id)
        self.name        = name
        self.lat         = lat
        self.lon         = lon
        self.base_demand = base_demand
        self.waiting     = 0
        self.x_px: float = 0.0
        self.y_px: float = 0.0

    # update (tick, dt): Spawn arriving passengers each tick based on demand
    def update(self, tick: int, dt: float):
        if not self.active:
            return
        arrivals_per_tick = self.base_demand / 288.0
        noise    = 1.0 + random.gauss(0, 0.1)
        new_arrivals = max(0, int(arrivals_per_tick * noise))
        self.waiting = min(self.waiting + new_arrivals, 500)

    # board (capacity): Transfer passengers onto a vehicle; return count boarded
    def board(self, capacity: int) -> int:
        boarded      = min(self.waiting, capacity)
        self.waiting -= boarded
        return boarded