# Rule-Based v2
# ridership_system: Computes synthetic daily ridership using the full SF modifier dataset.
#
# Design philosophy:
#   - Historical SFMTA ridership from the *sim year only* (2019) anchors every route baseline.
#   - ACS commute departure times shape the intra-day demand curve precisely.
#   - Land-use parcel counts weight per-stop demand spatially.
#   - Census population density scales total system demand.
#   - LODES commute-worker counts calibrate weekday vs. weekend asymmetry.
#   - Network topology (stop count, spacing, connectivity) adjusts relative route shares.
#   - All factors are bounded so no single data source can dominate the output.

import math
import random
from statistics import median
from typing import Dict, List, Optional

from game_world.entities.route          import RouteEntity
from game_world.entities.passenger_flow import PassengerFlow
from data.processors.aggregator         import Aggregator

import logging
log = logging.getLogger(__name__)


class RidershipSystem:

    # ------------------------------------------------------------------ init --

    def __init__(self, sim_config: dict, modifier_loader, aggregator: Aggregator):
        self._flow       = PassengerFlow(sim_config, modifier_loader)
        self._modifier   = modifier_loader
        self._aggregator = aggregator
        self._rng        = random.Random()
        self._cfg        = sim_config.get("simulation", {})

        # Tables built from 2019-only historical data
        self._month_factor:            Dict[int, float] = {}
        self._service_category_factor: Dict[str, float] = {}
        self._route_baseline_cache:    Dict[tuple, float] = {}

        # ACS-derived hour-weight table (built from commute departure CSV if available)
        self._acs_hour_weights: Dict[int, float] = {}

        # LODES-derived commute asymmetry scalar
        self._lodes_commute_scalar: float = 1.0

        self._build_all_tables()

    # --------------------------------------------------------- table builders --

    def _build_all_tables(self):
        """Build every calibration table from the modifier data."""
        self._build_calibration_tables()
        self._build_acs_hour_weights()
        self._build_lodes_scalar()

    def _build_calibration_tables(self):
        """Month and service-category multipliers derived from 2019 ridership only."""
        df = getattr(self._modifier, "ridership_df", None)
        if df is None or getattr(df, "empty", True):
            self._month_factor = {m: 1.0 for m in range(1, 13)}
            self._service_category_factor = {}
            return

        try:
            work = df.copy()

            # Year-segment guard: use the year exposed by the modifier (2019 by default)
            sim_year = getattr(self._modifier, "sim_year", 2019)
            if "Month" in work.columns:
                work = work[work["Month"].dt.year == sim_year].copy()

            if work.empty or "Average Daily Boardings" not in work.columns:
                self._month_factor = {m: 1.0 for m in range(1, 13)}
                self._service_category_factor = {}
                return

            boardings       = work["Average Daily Boardings"].dropna()
            overall_median  = max(float(boardings.median()) if not boardings.empty else 1.0, 1.0)

            # Month factors
            month_medians = (
                work.dropna(subset=["Month", "Average Daily Boardings"])
                    .groupby(work["Month"].dt.month)["Average Daily Boardings"]
                    .median()
                    .to_dict()
            )
            self._month_factor = {
                m: self._clamp(
                    float(month_medians.get(m, overall_median)) / overall_median,
                    0.70, 1.35
                )
                for m in range(1, 13)
            }

            # Service-category factors
            if "Service Category" in work.columns:
                cat_medians = (
                    work.dropna(subset=["Service Category", "Average Daily Boardings"])
                        .groupby("Service Category")["Average Daily Boardings"]
                        .median()
                        .to_dict()
                )
                self._service_category_factor = {
                    str(cat): self._clamp(float(val) / overall_median, 0.55, 1.65)
                    for cat, val in cat_medians.items()
                }
            else:
                self._service_category_factor = {}

        except Exception:
            log.exception("RB2: calibration table build failed")
            self._month_factor            = {m: 1.0 for m in range(1, 13)}
            self._service_category_factor = {}

    def _build_acs_hour_weights(self):
        """
        Build a {hour_int: weight} table from the ACS commute departure CSV.

        The CSV has rows like "5:00 a.m. to 5:29 a.m." with an estimate column.
        We bin those 30-minute windows into integer hours and normalise so the
        peak hour = 1.0; all other hours scale relative to it.
        """
        acs_df = getattr(self._modifier, "commute_df", None)
        if acs_df is None or getattr(acs_df, "empty", True):
            self._acs_hour_weights = {}
            return

        try:
            hour_totals: Dict[int, float] = {}

            for _, row in acs_df.iterrows():
                label    = str(row.get("label", "")).lower().strip()
                estimate = float(row.get("estimate", 0) or 0)
                if estimate <= 0:
                    continue

                # Parse the starting hour from labels like "7:00 a.m. to 7:29 a.m."
                hour = self._parse_acs_hour(label)
                if hour is not None:
                    hour_totals[hour] = hour_totals.get(hour, 0.0) + estimate

            if not hour_totals:
                self._acs_hour_weights = {}
                return

            peak = max(hour_totals.values())
            if peak <= 0:
                self._acs_hour_weights = {}
                return

            self._acs_hour_weights = {h: v / peak for h, v in hour_totals.items()}
            log.info(f"RB2: ACS hour weights built for {len(self._acs_hour_weights)} hours")

        except Exception:
            log.exception("RB2: ACS hour weight build failed")
            self._acs_hour_weights = {}

    @staticmethod
    def _parse_acs_hour(label: str) -> Optional[int]:
        """Return integer hour (0-23) from an ACS departure-time label, or None."""
        import re
        # Match patterns like "5:00 a.m." or "12:00 p.m."
        match = re.search(r"(\d{1,2}):(\d{2})\s*(a\.m\.|p\.m\.)", label)
        if not match:
            return None
        h, _, period = int(match.group(1)), int(match.group(2)), match.group(3)
        if period == "a.m.":
            return 0 if h == 12 else h
        else:
            return 12 if h == 12 else h + 12

    def _build_lodes_scalar(self):
        """
        Derive a weekday-vs-weekend demand asymmetry scalar from LODES total jobs.
        Assumes each commute job generates ~1 boardings/day on the system.
        Stored as a ratio relative to a 500k-worker reference.
        """
        workers = getattr(self._modifier, "commute_workers", 0)
        if workers > 0:
            # San Francisco reference: ~500k commute workers driving weekday peaks
            self._lodes_commute_scalar = self._clamp(workers / 500_000, 0.60, 2.00)
        else:
            self._lodes_commute_scalar = 1.0
        log.info(f"RB2: LODES commute scalar = {self._lodes_commute_scalar:.3f}")

    # ------------------------------------------------------- helper utilities --

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _month_effect(self, month_int: int) -> float:
        return self._month_factor.get(month_int, 1.0)

    def _service_effect(self, service_category: str) -> float:
        return self._service_category_factor.get(service_category, 1.0)

    # ----------------------------------------------- ACS temporal demand curve --

    def _acs_temporal_factor(self, hour: float) -> float:
        """
        Scale demand based on the observed ACS departure distribution.
        Falls back to a smooth parametric curve if the ACS table is empty.
        """
        if self._acs_hour_weights:
            h = int(hour) % 24
            raw = self._acs_hour_weights.get(h, 0.05)
            # Transit demand lags departure time by ~30 min; bleed into adjacent hour
            next_h = (h + 1) % 24
            blended = 0.65 * raw + 0.35 * self._acs_hour_weights.get(next_h, raw)
            # Evening return trip: mirror of morning peak scaled down
            evening_h = (h - 10) % 24
            evening   = 0.80 * self._acs_hour_weights.get(evening_h, 0.0)
            combined  = max(blended, evening)
            return self._clamp(combined * 1.4, 0.05, 1.40)

        # Parametric fallback: bimodal AM/PM curve
        am_peak = math.exp(-0.5 * ((hour - 8.0) / 1.2) ** 2)
        pm_peak = math.exp(-0.5 * ((hour - 17.5) / 1.4) ** 2)
        night   = 0.15 * math.exp(-0.5 * ((hour - 23.0) / 2.0) ** 2)
        return self._clamp(max(am_peak, pm_peak, night, 0.05), 0.05, 1.20)

    # ------------------------------------------- land-use spatial demand weight --

    def _land_use_route_weight(self, route: RouteEntity) -> float:
        """
        Weight a route by the residential+mixed residential parcel share in the
        SF land-use dataset. More residential parcels near the route → higher demand.
        """
        land_use = getattr(self._modifier, "land_use_counts", {})
        if not land_use:
            return 1.0

        total     = sum(land_use.values()) or 1
        res       = land_use.get("RESIDENT", 0) + land_use.get("MIXRES", 0)
        mixed_com = land_use.get("MIPS", 0) + land_use.get("CIE", 0) + land_use.get("RETAIL", 0)

        # Routes penetrating high-residential areas get a modest demand boost
        res_share = res / total
        com_share = mixed_com / total

        # SF-specific baseline: ~44% residential, ~14% commercial/institutional
        res_factor = 0.90 + 0.40 * (res_share / 0.44)
        com_factor = 1.00 + 0.25 * (com_share / 0.14)

        return self._clamp(res_factor * com_factor, 0.75, 1.40)

    # ----------------------------------------------- route geometry factors --

    def _route_catchment_mass(self, route: RouteEntity) -> float:
        if not route.stations:
            return 0.0
        return sum(max(float(getattr(s, "base_demand", 0.0)), 0.0) for s in route.stations)

    def _route_stop_count_effect(self, route: RouteEntity) -> float:
        n = len(route.stations)
        if n <= 0:
            return 0.50
        # Log-linear access effect: 10 stops → ~1.06, 30 stops → ~1.26
        return self._clamp(0.88 + 0.20 * math.log1p(n / 5.0), 0.80, 1.40)

    def _route_spacing_effect(self, route: RouteEntity) -> float:
        """Reward stop spacings consistent with SF urban density (~250–500 m = 0.002–0.005 deg)."""
        if len(route.stations) < 2:
            return 0.85
        dists, prev = [], route.stations[0]
        for cur in route.stations[1:]:
            dx = float(getattr(cur, "lat", 0.0)) - float(getattr(prev, "lat", 0.0))
            dy = float(getattr(cur, "lon", 0.0)) - float(getattr(prev, "lon", 0.0))
            dists.append(math.sqrt(dx * dx + dy * dy))
            prev = cur
        avg = sum(dists) / len(dists) if dists else 0.0
        if avg <= 0:         return 0.88
        if avg < 0.002:      return 0.90   # stops too close together
        if avg < 0.005:      return 1.05   # ideal SF street spacing
        if avg < 0.012:      return 1.00   # acceptable
        if avg < 0.030:      return 0.93   # wider spacing — less walkable
        return 0.85                         # very sparse route

    def _route_connectivity_effect(self, route: RouteEntity,
                                    routes: List[RouteEntity]) -> float:
        if not route.stations:
            return 0.80
        network_ids = {s.entity_id for r in routes for s in r.stations}
        network_count = max(len(network_ids), 1)
        route_count = len({s.entity_id for s in route.stations})
        share = route_count / network_count
        return self._clamp(0.85 + 0.90 * math.sqrt(share), 0.85, 1.25)

    def _route_network_share(self, route: RouteEntity,
                              routes: List[RouteEntity]) -> float:
        masses     = [self._route_catchment_mass(r) for r in routes]
        total_mass = sum(masses)
        if total_mass <= 0:
            return 1.0 / max(len(routes), 1)
        return self._clamp(self._route_catchment_mass(route) / total_mass, 0.002, 0.60)

    # ------------------------------------------------- supply-side factors --

    def _trip_supply_effect(self, route: RouteEntity) -> float:
        trips = max(int(getattr(route, "total_trips", 0)), 0)
        if trips <= 0:
            trips = max(1, len(route.stations) // 6)
        return self._clamp(0.82 + 0.18 * math.log1p(trips), 0.85, 1.30)

    # ------------------------------------------ historical baseline anchor --

    def _safe_route_baseline(self, route: RouteEntity, day_type: str) -> float:
        """
        2019-only historical median for this route/day-type.
        Falls back through: route median → category default → floor.
        """
        key = (route.short_name, day_type)
        if key in self._route_baseline_cache:
            return self._route_baseline_cache[key]

        baseline = 0.0
        try:
            baseline = float(self._modifier.get_route_baseline(route.short_name, day_type))
        except Exception:
            pass

        if baseline < 10:
            baseline = self._category_default(route.service_category, day_type)

        baseline = max(baseline, 25.0)
        self._route_baseline_cache[key] = baseline
        return baseline

    def _category_default(self, service_category: str, day_type: str) -> float:
        base = {
            "Bus":             2_800.0,
            "Light Rail":      5_500.0,
            "Tram/Light Rail": 5_500.0,
            "Subway":         11_000.0,
            "Cable Car":       1_600.0,
        }.get(service_category, 2_800.0)

        day_factor = {"Weekday": 1.00, "Saturday": 0.73, "Sunday": 0.58}.get(day_type, 1.00)

        # Amplify by commute scalar on weekdays only
        commute_boost = self._lodes_commute_scalar if day_type == "Weekday" else 1.0
        return base * day_factor * commute_boost * self._service_category_factor.get(service_category, 1.0)

    # ------------------------------------------------------- feedback terms --

    def _observed_boarding_effect(self, route: RouteEntity, baseline: float) -> float:
        observed = float(max(getattr(route, "daily_boardings", 0), 0))
        if observed <= 0 or baseline <= 0:
            return 1.0
        ratio = observed / baseline
        return self._clamp(0.85 + 0.15 * ratio, 0.85, 1.20)

    def _network_balance_effect(self, route: RouteEntity,
                                 routes: List[RouteEntity]) -> float:
        peers = [
            float(max(getattr(r, "daily_boardings", 0), 0))
            for r in routes
            if r.service_category == route.service_category
        ]
        if not peers:
            return 1.0
        med = median(peers)
        if med <= 0:
            return 1.0
        obs = float(max(getattr(route, "daily_boardings", 0), 0))
        if obs <= 0:
            return 1.0
        return self._clamp(0.90 + 0.10 * (obs / med), 0.90, 1.15)

    def _route_noise(self) -> float:
        return self._clamp(1.0 + self._rng.gauss(0, 0.045), 0.85, 1.15)

    # ------------------------------------------------- core composition --

    def _compose_synthetic(self, route: RouteEntity, routes: List[RouteEntity],
                           day_type: str, month_int: int, hour: float,
                           global_demand: float, global_noise: float) -> float:

        baseline       = self._safe_route_baseline(route, day_type)
        month_effect   = self._month_effect(month_int)
        service_effect = self._service_effect(route.service_category)
        supply_effect  = self._trip_supply_effect(route)
        temporal_fx    = self._acs_temporal_factor(hour)
        land_use_fx    = self._land_use_route_weight(route)
        connectivity   = self._route_connectivity_effect(route, routes)
        spacing_fx     = self._route_spacing_effect(route)
        stop_count_fx  = self._route_stop_count_effect(route)
        observed_fx    = self._observed_boarding_effect(route, baseline)
        network_fx     = self._network_balance_effect(route, routes)
        route_noise    = self._route_noise()

        # Commute asymmetry: weekday demand is boosted by LODES worker density
        commute_scalar = self._lodes_commute_scalar if day_type == "Weekday" else 1.0

        synthetic = (
            baseline
            * global_demand       # PassengerFlow day_type + seasonal + peak factor
            * global_noise        # system-wide Gaussian noise
            * month_effect        # 2019 monthly calibration
            * service_effect      # category-level calibration
            * supply_effect       # trip supply (vehicles in service)
            * temporal_fx         # ACS departure-time shape
            * land_use_fx         # SF land-use spatial weight
            * connectivity        # network topology
            * spacing_fx          # stop-spacing plausibility
            * stop_count_fx       # access coverage
            * observed_fx         # live boarding feedback
            * network_fx          # cross-route balance
            * commute_scalar      # LODES worker density asymmetry
            * route_noise         # per-route stochastic variation
        )

        # Clip to a 2019-data-informed range
        low  = baseline * 0.30
        high = baseline * 2.80

        return float(round(self._clamp(synthetic, low, high)))

    # ------------------------------------------------- public interface --

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
