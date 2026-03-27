"""
Filename: ridership_system.py
Author: Ayemhenre Isikhuemhen
Description: Drives daily ridership tallying — queries modifier baselines,
             applies PassengerFlow factors, and feeds the Aggregator each day.
Last Updated: March, 2026
"""

# Libraries
import random
from typing import List

# Modules
from game_world.entities.route import RouteEntity
from game_world.entities.passenger_flow import PassengerFlow
from data.processors.aggregator import Aggregator


# RidershipSystem: Called once per sim day to compute and record route boardings
class RidershipSystem:

    # __init__ (sim_config, modifier_loader, aggregator)
    def __init__(self, sim_config: dict, modifier_loader, aggregator: Aggregator):
        self._flow       = PassengerFlow(sim_config, modifier_loader)
        self._modifier   = modifier_loader
        self._aggregator = aggregator
        self._rng        = random.Random()

    # process_day (routes, month_label, day_type, month_int, hour)
    def process_day(self, routes: List[RouteEntity], month_label: str,
                    day_type: str, month_int: int, hour: float = 12.0):
        demand = self._flow.demand_factor(hour, day_type, month_int)
        noise  = self._flow.noise_factor(self._rng)

        for route in routes:
            baseline = self._modifier.get_route_baseline(route.short_name, day_type)
            if baseline < 10:
                baseline = max(route.daily_boardings, 50)

            synthetic_boardings = round(baseline * demand * noise)
            self._aggregator.record_day(
                month_label,
                route.short_name,
                route.service_category,
                day_type,
                float(synthetic_boardings),
            )
            route.reset_day()