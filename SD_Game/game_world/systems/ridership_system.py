# ridership_system: Computes and records synthetic daily ridership for every route once per sim day.

import math
import random
from typing import List, Dict

from game_world.entities.route          import RouteEntity
from game_world.entities.passenger_flow import PassengerFlow
from data.processors.aggregator         import Aggregator


# RidershipSystem: Uses network structure, stop demand, and operating rules to produce synthetic boardings.
class RidershipSystem:

    def __init__(self, sim_config: dict, modifier_loader, aggregator: Aggregator):
        self._flow       = PassengerFlow(sim_config, modifier_loader)
        self._modifier   = modifier_loader
        self._aggregator = aggregator
        self._rng        = random.Random()

        # Weak calibration tables derived from the historical ridership file
        self._month_factor:            Dict[int, float] = {}
        self._service_category_factor: Dict[str, float] = {}

        self._build_calibration_tables()

    # _build_calibration_tables: Derive soft calibration multipliers from the historical ridership file.
    def _build_calibration_tables(self):
        df = getattr(self._modifier, "ridership_df", None)
        if df is None or getattr(df, "empty", True):
            self._month_factor = {m: 1.0 for m in range(1, 13)}
            self._service_category_factor = {}
            return

        try:
            work = df.copy()

            if "Average Daily Boardings" not in work.columns:
                self._month_factor = {m: 1.0 for m in range(1, 13)}
                self._service_category_factor = {}
                return

            boardings = work["Average Daily Boardings"].dropna()
            overall_median = float(boardings.median()) if not boardings.empty else 1.0
            overall_median = max(overall_median, 1.0)

            if "Month" in work.columns:
                month_medians = (
                    work.dropna(subset=["Month", "Average Daily Boardings"])
                        .groupby(work["Month"].dt.month)["Average Daily Boardings"]
                        .median()
                        .to_dict()
                )
                self._month_factor = {
                    m: self._clamp(float(month_medians.get(m, overall_median)) / overall_median,
                                   0.80, 1.20)
                    for m in range(1, 13)
                }
            else:
                self._month_factor = {m: 1.0 for m in range(1, 13)}

            if "Service Category" in work.columns:
                cat_medians = (
                    work.dropna(subset=["Service Category", "Average Daily Boardings"])
                        .groupby("Service Category")["Average Daily Boardings"]
                        .median()
                        .to_dict()
                )
                self._service_category_factor = {
                    str(cat): self._clamp(float(val) / overall_median, 0.75, 1.30)
                    for cat, val in cat_medians.items()
                }
            else:
                self._service_category_factor = {}

        except Exception:
            self._month_factor = {m: 1.0 for m in range(1, 13)}
            self._service_category_factor = {}

    # _clamp: Bound a float between low and high.
    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    # _service_mode_factor: Relative propensity to ride by transit mode.
    def _service_mode_factor(self, service_category: str) -> float:
        base = {
            "Bus":             1.00,
            "Tram/Light Rail": 1.10,
            "Subway":          1.35,
            "Cable Car":       0.75,
        }.get(service_category, 1.00)
        return base * self._service_category_factor.get(service_category, 1.0)

    # _route_catchment_mass: Total demand accessible along the route from all served stations.
    def _route_catchment_mass(self, route: RouteEntity) -> float:
        if not route.stations:
            return 0.0
        return sum(max(float(getattr(s, "base_demand", 0.0)), 0.0) for s in route.stations)

    # _route_stop_count_effect: More stops increase access, but with diminishing returns.
    def _route_stop_count_effect(self, route: RouteEntity) -> float:
        n = len(route.stations)
        if n <= 0:
            return 0.50
        return self._clamp(0.70 + 0.18 * math.log1p(n), 0.70, 1.45)

    # _route_spacing_effect: Reward routes whose stop spacing is neither too short nor too sparse.
    def _route_spacing_effect(self, route: RouteEntity) -> float:
        if len(route.stations) < 2:
            return 0.85

        dists = []
        prev = route.stations[0]
        for cur in route.stations[1:]:
            dx = float(getattr(cur, "lat", 0.0)) - float(getattr(prev, "lat", 0.0))
            dy = float(getattr(cur, "lon", 0.0)) - float(getattr(prev, "lon", 0.0))
            dists.append(math.sqrt(dx * dx + dy * dy))
            prev = cur

        avg_dist = sum(dists) / len(dists) if dists else 0.0

        # Penalise routes that look implausibly dense or implausibly sparse
        if avg_dist <= 0:
            return 0.90
        if avg_dist < 0.002:
            return 0.93
        if avg_dist > 0.030:
            return 0.88
        return 1.00

    # _route_connectivity_effect: Reward routes that touch more unique stations in the network.
    def _route_connectivity_effect(self, route: RouteEntity, routes: List[RouteEntity]) -> float:
        if not route.stations:
            return 0.80

        network_station_count = len({
            s.entity_id
            for r in routes
            for s in r.stations
        })
        network_station_count = max(network_station_count, 1)

        unique_route_stations = len({s.entity_id for s in route.stations})
        share = unique_route_stations / network_station_count

        return self._clamp(0.85 + 0.90 * math.sqrt(share), 0.85, 1.25)

    # _route_supply_effect: Use active service supply as a primary generator rather than a minor correction.
    def _route_supply_effect(self, route: RouteEntity) -> float:
        trips = max(int(getattr(route, "total_trips", 0)), 0)

        if trips <= 0:
            # If the route did not log trips, infer a weak supply effect from route size
            trips = max(1, len(route.stations) // 6)

        return self._clamp(0.80 + 0.16 * math.log1p(trips), 0.85, 1.35)

    # _route_boarding_feedback: Use live system usage as a bounded endogenous feedback term.
    def _route_boarding_feedback(self, route: RouteEntity, demand_scale: float) -> float:
        observed = float(max(getattr(route, "daily_boardings", 0), 0.0))

        if observed <= 0:
            return 1.0

        scaled = observed / max(demand_scale, 1.0)
        return self._clamp(0.92 + 0.08 * math.log1p(scaled), 0.92, 1.18)

    # _route_network_share: Share of network-accessible demand captured by this route.
    def _route_network_share(self, route: RouteEntity, routes: List[RouteEntity]) -> float:
        masses = [self._route_catchment_mass(r) for r in routes]
        total_mass = sum(masses)

        if total_mass <= 0:
            count = max(len(routes), 1)
            return 1.0 / count

        route_mass = self._route_catchment_mass(route)
        share = route_mass / total_mass

        # Floors prevent tiny routes from collapsing to zero in the synthetic output
        return self._clamp(share, 0.002, 0.60)

    # _system_demand_scale: Convert system-wide stop demand into the total number of boardings expected today.
    def _system_demand_scale(self, routes: List[RouteEntity], day_type: str,
                             month_int: int, hour: float) -> float:
        unique_stations = {}
        for route in routes:
            for station in route.stations:
                unique_stations[station.entity_id] = station

        total_station_demand = sum(
            max(float(getattr(station, "base_demand", 0.0)), 0.0)
            for station in unique_stations.values()
        )

        demand_factor = self._flow.demand_factor(hour, day_type, month_int)
        noise_factor  = self._flow.noise_factor(self._rng)
        month_factor  = self._month_factor.get(month_int, 1.0)

        # Base conversion from station-side arrivals to route boardings
        return max(total_station_demand * demand_factor * noise_factor * month_factor, 50.0)

    # _historical_anchor: Weak historical calibration only; transit mechanics remain primary.
    def _historical_anchor(self, route: RouteEntity, day_type: str) -> float:
        try:
            baseline = float(self._modifier.get_route_baseline(route.short_name, day_type))
        except Exception:
            baseline = 0.0

        if baseline < 10:
            return 0.0

        return baseline

    # _compose_synthetic: Generate one route's boardings from network mechanics and soft calibration.
    def _compose_synthetic(self, route: RouteEntity, routes: List[RouteEntity],
                           day_type: str, month_int: int, hour: float,
                           system_scale: float) -> float:
        share              = self._route_network_share(route, routes)
        mode_factor        = self._service_mode_factor(route.service_category)
        stop_count_effect  = self._route_stop_count_effect(route)
        spacing_effect     = self._route_spacing_effect(route)
        connectivity_fx    = self._route_connectivity_effect(route, routes)
        supply_effect      = self._route_supply_effect(route)
        boarding_feedback  = self._route_boarding_feedback(route, system_scale)
        route_noise        = self._clamp(1.0 + self._rng.gauss(0, 0.04), 0.90, 1.12)

        synthetic = (
            system_scale
            * share
            * mode_factor
            * stop_count_effect
            * spacing_effect
            * connectivity_fx
            * supply_effect
            * boarding_feedback
            * route_noise
        )

        # Softly calibrate to history without letting history dominate the generator
        historical = self._historical_anchor(route, day_type)
        if historical > 0:
            synthetic = 0.85 * synthetic + 0.15 * historical

        # Keep outputs plausible but still allow real variation
        low_floor = max(20.0, self._route_catchment_mass(route) * 0.10)
        high_cap  = max(low_floor + 10.0, self._route_catchment_mass(route) * 4.50)

        return float(round(self._clamp(synthetic, low_floor, high_cap)))

    # process_day: Compute one day's synthetic boardings per route and send them to the aggregator.
    def process_day(self, routes: List[RouteEntity], month_label: str,
                    day_type: str, month_int: int, hour: float = 12.0):
        system_scale = self._system_demand_scale(routes, day_type, month_int, hour)

        for route in routes:
            synthetic = self._compose_synthetic(
                route=route,
                routes=routes,
                day_type=day_type,
                month_int=month_int,
                hour=hour,
                system_scale=system_scale,
            )

            self._aggregator.record_day(
                month_label,
                route.short_name,
                route.service_category,
                day_type,
                synthetic,
            )
            route.reset_day()