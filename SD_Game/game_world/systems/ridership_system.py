# ridership_system: Computes and records synthetic daily ridership for every route once per sim day.

import random
from typing import List

from game_world.entities.route          import RouteEntity
from game_world.entities.passenger_flow import PassengerFlow
from data.processors.aggregator         import Aggregator


# RidershipSystem: Uses historical baselines and demand factors to produce synthetic boardings.
class RidershipSystem:

    def __init__(self, sim_config: dict, modifier_loader, aggregator: Aggregator):
        self._flow       = PassengerFlow(sim_config, modifier_loader)
        self._modifier   = modifier_loader
        self._aggregator = aggregator
        self._rng        = random.Random()

    # process_day: Compute one day's synthetic boardings per route and send them to the aggregator.
    def process_day(self, routes: List[RouteEntity], month_label: str,
                    day_type: str, month_int: int, hour: float = 12.0):
        demand = self._flow.demand_factor(hour, day_type, month_int)
        noise  = self._flow.noise_factor(self._rng)

        for route in routes:
            # Historical median anchors the output; entity counter is a last resort
            baseline = self._modifier.get_route_baseline(route.short_name, day_type)
            if baseline < 10:
                baseline = max(route.daily_boardings, 50)

            synthetic = round(baseline * demand * noise)
            self._aggregator.record_day(
                month_label,
                route.short_name,
                route.service_category,
                day_type,
                float(synthetic),
            )
            route.reset_day()
