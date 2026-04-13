# graph_builder: Converts a GTFSProcessor into RouteEntity and Station objects with shape data.

from typing import Dict, List, Tuple
import logging

from data.processors.gtfs_processor import GTFSProcessor
from game_world.entities.route import RouteEntity
from game_world.entities.station import Station

log = logging.getLogger(__name__)

# Four display categories — these are the only colours used on the map
_TYPE_LABEL = {
    0: "Light Rail",
    1: "Subway",
    3: "Bus",
    5: "Cable Car",
}

_TYPE_COLOR = {
    0: (191, 138, 32),  # Light Rail  - amber
    1: (175, 42, 58),   # Subway      - red
    3: (50, 120, 210),  # Bus         - blue
    5: (122, 42, 175),  # Cable Car   - purple
}


class GraphBuilder:

    def __init__(self, processor: GTFSProcessor, max_routes: int = 80):
        self._proc = processor
        self._max_routes = max_routes

    def build(self) -> Tuple[List[RouteEntity], List[Station], Dict[str, Station]]:
        proc = self._proc

        shape_index = self._build_shape_index()
        route_shape = self._build_route_shape_map(shape_index)

        stop_index: Dict[str, Station] = {}
        routes: List[RouteEntity] = []
        type_counts: Dict[int, int] = {}

        # --- GROUP ROUTES WITH ROBUST CLASSIFICATION ---
        routes_by_type: Dict[int, List] = {}

        for r in proc.feed.routes:
            rt = self._classify_route(r)
            routes_by_type.setdefault(rt, []).append(r)

        # Sort to prioritize main routes
        def route_sort_key(r):
            name = r.route_short_name or ""
            return (not name.isdigit(), name)

        for rt in routes_by_type:
            routes_by_type[rt].sort(key=route_sort_key)

        # Balanced selection
        num_types = len(routes_by_type)
        per_type_cap = max(1, self._max_routes // max(1, num_types))

        selected_routes = []
        for rt, group in routes_by_type.items():
            selected_routes.extend(group[:per_type_cap])

        # Fill remaining if needed
        if len(selected_routes) < self._max_routes:
            remaining = [r for r in proc.feed.routes if r not in selected_routes]
            selected_routes.extend(remaining[: self._max_routes - len(selected_routes)])

        # --- BUILD ENTITIES ---
        for gtfs_route in selected_routes:
            stops = proc.get_route_stops(gtfs_route.route_id)
            if len(stops) < 2:
                continue

            rt = self._classify_route(gtfs_route)
            cat = _TYPE_LABEL.get(rt, "Bus")
            color = _TYPE_COLOR.get(rt, _TYPE_COLOR[3])

            entity = RouteEntity(
                route_id=gtfs_route.route_id,
                short_name=gtfs_route.route_short_name,
                long_name=gtfs_route.route_long_name,
                route_type=rt,
                service_category=cat,
            )
            entity.color = color

            for stop_id, lat, lon in stops:
                if stop_id not in stop_index:
                    gtfs_stop = proc.stop_index.get(stop_id)
                    name = gtfs_stop.stop_name if gtfs_stop else stop_id
                    s = Station(
                        stop_id=stop_id,
                        name=name,
                        lat=lat,
                        lon=lon,
                        base_demand=80.0,
                    )
                    stop_index[stop_id] = s

                entity.add_station(stop_index[stop_id])

            sid = route_shape.get(gtfs_route.route_id)
            if sid and sid in shape_index:
                entity.shape_polyline = shape_index[sid]

            routes.append(entity)
            type_counts[rt] = type_counts.get(rt, 0) + 1

        stations = list(stop_index.values())
        shaped = sum(1 for r in routes if r.shape_polyline)

        log.info(
            f"Graph: {len(routes)} routes "
            f"({type_counts.get(3, 0)} bus, "
            f"{type_counts.get(0, 0)} light rail, "
            f"{type_counts.get(5, 0)} cable car, "
            f"{type_counts.get(1, 0)} subway), "
            f"{len(stations)} stations, {shaped} with shape data"
        )

        return routes, stations, stop_index

    # classify route: sorts and organizes the transit types into four catagories
    def _classify_route(self, route) -> int:
        rt = route.route_type
        name = (route.route_short_name or "").upper()
        long_name = (route.route_long_name or "").upper()

        # Cable cars (very distinct)
        if rt == 5 or "CABLE" in long_name:
            return 5

        # SF Light Rail (J, K, L, M, N, T lines)
        if name in {"J", "K", "L", "M", "N", "T", "F"}:
            return 0

        # Bus substitutions for rail (KBUS, NBUS, etc.)
        if "BUS" in name and any(x in name for x in ["J", "K", "L", "M", "N", "T"]):
            return 3

        # Rapid / Express → still bus
        if "RAPID" in long_name or "EXPRESS" in long_name:
            return 3

        # Default GTFS mapping
        if rt in _TYPE_LABEL:
            return rt

        return 3  # fallback to bus

    def _build_shape_index(self) -> Dict[str, List[Tuple[float, float]]]:
        raw: Dict[str, List[Tuple[int, float, float]]] = {}

        for sp in self._proc.feed.shape_points:
            raw.setdefault(sp.shape_id, []).append((sp.sequence, sp.lat, sp.lon))

        result = {}
        for shape_id, pts in raw.items():
            pts.sort(key=lambda x: x[0])
            result[shape_id] = [(lat, lon) for _, lat, lon in pts]

        log.debug(f"Shape index: {len(result)} shapes")
        return result

    def _build_route_shape_map(self, shape_index: Dict) -> Dict[str, str]:
        route_trips: Dict[str, List] = {}

        for trip in self._proc.feed.trips:
            route_trips.setdefault(trip.route_id, []).append(trip)

        route_shape = {}
        for route_id, trips in route_trips.items():
            shaped = [t for t in trips if t.shape_id and t.shape_id in shape_index]

            if shaped:
                best = max(shaped, key=lambda t: len(shape_index.get(t.shape_id, [])))
                route_shape[route_id] = best.shape_id

        return route_shape