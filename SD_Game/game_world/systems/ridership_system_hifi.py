# ridership_system_hifi.py
# High-Fidelity generation model.
# Uses historical baselines as the primary anchor for each route, with month
# effects, service-category calibration, supply, live feedback, and network
# balance applied as multipliers on top. History drives the output; mechanics
# correct for conditions the history doesn't capture.

import math
import random
from statistics import median
from typing import Dict, List

from game_world.entities.route          import RouteEntity
from game_world.entities.passenger_flow import PassengerFlow
from data.processors.aggregator         import Aggregator


class RidershipSystem:

    def __init__(self, sim_config: dict, modifier_loader, aggregator: Aggregator):
        self._flow       = PassengerFlow(sim_config, modifier_loader)
        self._modifier   = modifier_loader
        self._aggregator = aggregator
        self._rng        = random.Random()

        self._month_factor:            Dict[int, float] = {}
        self._service_category_factor: Dict[str, float] = {}

        self._build_calibration_tables()

    def _build_calibration_tables(self):
        df = getattr(self._modifier, "ridership_df", None)
        if df is None or getattr(df, "empty", True):
            self._month_factor = {m: 1.0 for m in range(1, 13)}
            self._service_category_factor = {}
            return

        try:
            work = df.copy()

            needed = ["Average Daily Boardings", "Month"]
            if not all(col in work.columns for col in needed):
                self._month_factor = {m: 1.0 for m in range(1, 13)}
                self._service_category_factor = {}
                return

            boardings      = work["Average Daily Boardings"].dropna()
            overall_median = float(boardings.median()) if not boardings.empty else 1.0
            overall_median = max(overall_median, 1.0)

            month_medians = (
                work.dropna(subset=["Month", "Average Daily Boardings"])
                    .groupby(work["Month"].dt.month)["Average Daily Boardings"]
                    .median()
                    .to_dict()
            )
            self._month_factor = {
                m: self._clamp(
                    float(month_medians.get(m, overall_median)) / overall_median,
                    0.70, 1.35,
                )
                for m in range(1, 13)
            }

            if "Service Category" in work.columns:
                cat_medians = (
                    work.dropna(subset=["Service Category", "Average Daily Boardings"])
                        .groupby("Service Category")["Average Daily Boardings"]
                        .median()
                        .to_dict()
                )
                self._service_category_factor = {
                    str(cat): self._clamp(float(val) / overall_median, 0.60, 1.60)
                    for cat, val in cat_medians.items()
                }
            else:
                self._service_category_factor = {}

        except Exception:
            self._month_factor            = {m: 1.0 for m in range(1, 13)}
            self._service_category_factor = {}

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _safe_route_baseline(self, route: RouteEntity, day_type: str) -> float:
        baseline = 0.0
        try:
            baseline = float(self._modifier.get_route_baseline(route.short_name, day_type))
        except Exception:
            pass

        if baseline < 10:
            baseline = self._category_default(route.service_category, day_type)

        observed = float(max(route.daily_boardings, 0))
        if observed > 0:
            baseline = 0.85 * baseline + 0.15 * observed

        return max(baseline, 25.0)

    def _category_default(self, service_category: str, day_type: str) -> float:
        base = {
            "Bus":             3000.0,
            "Tram/Light Rail": 5500.0,
            "Subway":         12000.0,
            "Cable Car":       1800.0,
        }.get(service_category, 3000.0)
        day_factor = {"Weekday": 1.00, "Saturday": 0.74, "Sunday": 0.60}.get(day_type, 1.00)
        cat_factor = self._service_category_factor.get(service_category, 1.0)
        return base * day_factor * cat_factor

    def _month_effect(self, month_int: int) -> float:
        return self._month_factor.get(month_int, 1.0)

    def _service_effect(self, service_category: str) -> float:
        return self._service_category_factor.get(service_category, 1.0)

    def _trip_supply_effect(self, route: RouteEntity) -> float:
        trips = max(int(getattr(route, "total_trips", 0)), 0)
        if trips <= 0:
            return 1.0
        return self._clamp(0.82 + 0.18 * math.log1p(trips), 0.85, 1.30)

    def _observed_boarding_effect(self, route: RouteEntity, baseline: float) -> float:
        observed = float(max(getattr(route, "daily_boardings", 0), 0))
        if observed <= 0 or baseline <= 0:
            return 1.0
        ratio = observed / baseline
        return self._clamp(0.85 + 0.15 * ratio, 0.85, 1.20)

    def _network_balance_effect(self, route: RouteEntity,
                                 routes: List[RouteEntity]) -> float:
        values = [
            float(max(getattr(r, "daily_boardings", 0), 0))
            for r in routes
            if r.service_category == route.service_category
        ]
        if not values:
            return 1.0
        med = median(values)
        if med <= 0:
            return 1.0
        obs = float(max(getattr(route, "daily_boardings", 0), 0))
        if obs <= 0:
            return 1.0
        return self._clamp(0.90 + 0.10 * (obs / med), 0.90, 1.15)

    def _route_noise(self) -> float:
        return self._clamp(1.0 + self._rng.gauss(0, 0.05), 0.85, 1.15)

    def _compose_synthetic(self, route: RouteEntity, routes: List[RouteEntity],
                           day_type: str, month_int: int, hour: float,
                           global_demand: float, global_noise: float) -> float:
        baseline       = self._safe_route_baseline(route, day_type)
        month_effect   = self._month_effect(month_int)
        service_effect = self._service_effect(route.service_category)
        supply_effect  = self._trip_supply_effect(route)
        observed_fx    = self._observed_boarding_effect(route, baseline)
        network_fx     = self._network_balance_effect(route, routes)
        route_noise    = self._route_noise()

        synthetic = (
            baseline
            * global_demand
            * global_noise
            * month_effect
            * service_effect
            * supply_effect
            * observed_fx
            * network_fx
            * route_noise
        )

        low  = baseline * 0.35
        high = baseline * 2.60
        return float(round(self._clamp(synthetic, low, high)))

    def process_day(self, routes: List[RouteEntity], month_label: str,
                    day_type: str, month_int: int, hour: float = 12.0):
        global_demand = self._flow.demand_factor(hour, day_type, month_int)
        global_noise  = self._flow.noise_factor(self._rng)

        for route in routes:
            synthetic = self._compose_synthetic(
                route=route,
                routes=routes,
                day_type=day_type,
                month_int=month_int,
                hour=hour,
                global_demand=global_demand,
                global_noise=global_noise,
            )
            self._aggregator.record_day(
                month_label,
                route.short_name,
                route.service_category,
                day_type,
                synthetic,
            )
            route.reset_day()
