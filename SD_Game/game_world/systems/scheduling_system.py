# scheduling_system: Spawns and manages Vehicle instances per route; adds extra vehicles during peak hours.

from typing import Dict, List
import logging

from game_world.entities.route   import RouteEntity
from game_world.entities.vehicle import Vehicle

log = logging.getLogger(__name__)


# SchedulingSystem: Maintains one vehicle per route off-peak and three during AM/PM peaks.
class SchedulingSystem:

    def __init__(self, sim_config: dict, capacity: int = 60):
        self._capacity  = capacity
        self._peak      = sim_config["simulation"]["peak_boost"]
        self.vehicles:  Dict[str, List[Vehicle]] = {}
        self._v_counter = 0

    # initialise: Seed one vehicle per route at simulation start.
    def initialise(self, routes: List[RouteEntity]):
        for route in routes:
            if len(route.stations) >= 2:
                self.vehicles[route.entity_id] = [self._spawn(route)]

    # update: Bring each route up to the target vehicle count for the current hour.
    def update(self, routes: List[RouteEntity], hour: float):
        pk      = self._peak
        in_peak = (pk["am_start"] <= hour < pk["am_end"] or
                   pk["pm_start"] <= hour < pk["pm_end"])
        target  = 3 if in_peak else 1

        for route in routes:
            pool = self.vehicles.setdefault(route.entity_id, [])
            while len(pool) < target:
                pool.append(self._spawn(route, offset=len(pool)))

    # all_vehicles: Flat list of every active Vehicle across all routes.
    def all_vehicles(self) -> List[Vehicle]:
        result = []
        for pool in self.vehicles.values():
            result.extend(v for v in pool if v.active)
        return result

    # _spawn: Create a new Vehicle staggered along the route by offset fraction.
    def _spawn(self, route: RouteEntity, offset: int = 0) -> Vehicle:
        self._v_counter += 1
        v = Vehicle(
            vehicle_id=f"v{self._v_counter}_{route.short_name}",
            route=route,
            capacity=self._capacity,
        )
        # Stagger multiple vehicles evenly around the route at spawn time
        if len(route.stations) > 2:
            v._stop_idx = (
                offset * max(1, len(route.stations) // 3)
            ) % len(route.stations)
        return v
