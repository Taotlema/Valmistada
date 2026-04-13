# station: One GTFS stop on the map with a waiting passenger pool.

import random
from game_world.entities.base_entity import BaseEntity


# Station: Spawns arriving passengers each tick and lets vehicles board them.
class Station(BaseEntity):

    def __init__(self, stop_id: str, name: str, lat: float, lon: float,
                 base_demand: float = 100.0):
        super().__init__(entity_id=stop_id)
        self.name        = name
        self.lat         = lat
        self.lon         = lon
        self.base_demand = base_demand   # daily passenger arrivals before modifiers
        self.waiting     = 0
        self.x_px: float = 0.0           # pixel coords set by RendererAdapter
        self.y_px: float = 0.0

    # update: Spread daily demand evenly across 288 ticks with small Gaussian noise.
    def update(self, tick: int, dt: float):
        if not self.active:
            return
        arrivals = max(0, int((self.base_demand / 288.0) * (1.0 + random.gauss(0, 0.1))))
        # Cap waiting passengers to avoid unbounded growth during pauses
        self.waiting = min(self.waiting + arrivals, 500)

    # board: Transfer up to capacity passengers onto a vehicle; return count boarded.
    def board(self, capacity: int) -> int:
        boarded      = min(self.waiting, capacity)
        self.waiting -= boarded
        return boarded
