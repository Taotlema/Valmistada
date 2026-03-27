"""
Filename: scheduling_system.py
Author: Ayemhenre Isikhuemhen
Description: Spawns and retires Vehicle instances on routes according to
             the simulated time of day — more vehicles during peak hours.
Last Updated: March, 2026
"""

# Libraries
from typing import Dict, List
import logging

# Modules
from game_world.entities.route import RouteEntity
from game_world.entities.vehicle import Vehicle

log = logging.getLogger(__name__)


# SchedulingSystem: Manages the active vehicle pool per route
class SchedulingSystem:

    # __init__ (sim_config, capacity: seats per vehicle)
    def __init__(self, sim_config: dict, capacity: int = 60):
        self._capacity = capacity
        self._peak     = sim_config["simulation"]["peak_boost"]
        self.vehicles: Dict[str, List[Vehicle]] = {}
        self._v_counter = 0

    # initialise (routes): Seed one vehicle per route at sim start
    def initialise(self, routes: List[RouteEntity]):
        for route in routes:
            if len(route.stations) >= 2:
                self.vehicles[route.entity_id] = [self._spawn(route)]

    # update (routes, hour): Add vehicles during peak windows
    def update(self, routes: List[RouteEntity], hour: float):
        peak    = self._peak
        in_peak = (peak["am_start"] <= hour < peak["am_end"] or
                   peak["pm_start"] <= hour < peak["pm_end"])

        for route in routes:
            pool   = self.vehicles.setdefault(route.entity_id, [])
            target = 3 if in_peak else 1
            while len(pool) < target:
                v = self._spawn(route, offset=len(pool))
                pool.append(v)

    # all_vehicles: Flat list of every active Vehicle across all routes
    def all_vehicles(self) -> List[Vehicle]:
        result = []
        for pool in self.vehicles.values():
            result.extend(v for v in pool if v.active)
        return result

    # _spawn (route, offset): Create a new staggered vehicle
    def _spawn(self, route: RouteEntity, offset: int = 0) -> Vehicle:
        self._v_counter += 1
        v = Vehicle(
            vehicle_id=f"v{self._v_counter}_{route.short_name}",
            route=route,
            capacity=self._capacity,
        )
        if len(route.stations) > 2:
            v._stop_idx = (offset * max(1, len(route.stations) // 3)) % len(route.stations)
        return v