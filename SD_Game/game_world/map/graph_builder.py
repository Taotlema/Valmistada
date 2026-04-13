# graph_builder: Converts a GTFSProcessor into RouteEntity and Station objects with shape data.

from typing import Dict, List, Tuple
import logging

from data.processors.gtfs_processor import GTFSProcessor
from game_world.entities.route   import RouteEntity
from game_world.entities.station import Station

log = logging.getLogger(__name__)

# route_type to service label mapping
_TYPE_LABEL = {
    0: "Tram/Light Rail",
    1: "Subway",
    3: "Bus",
    5: "Cable Car",
}

# route_type to RGB line colour used by the renderer
_TYPE_COLOR = {
    0: (191, 138,  32),   # Tram        - amber
    1: (175,  42,  58),   # Subway      - red
    3: ( 42, 106, 191),   # Bus         - blue
    5: (122,  42, 175),   # Cable Car   - purple
}

# Slightly distinct blue for bus vs tram so they read apart on screen
_BUS_COLOR  = ( 50, 120, 210)
_TRAM_COLOR = (191, 138,  32)


# GraphBuilder: Builds entity lists from GTFS data including shape polylines.
class GraphBuilder:

    def __init__(self, processor: GTFSProcessor, max_routes: int = 40):
        self._proc       = processor
        self._max_routes = max_routes

    # build: Return (routes, stations, stop_index) entity collections.
    def build(self) -> Tuple[List[RouteEntity], List[Station], Dict[str, Station]]:
        proc = self._proc

        shape_index = self._build_shape_index()
        route_shape = self._build_route_shape_map(shape_index)

        stop_index: Dict[str, Station] = {}
        routes:     List[RouteEntity]  = []

        for gtfs_route in proc.feed.routes[:self._max_routes]:
            stops = proc.get_route_stops(gtfs_route.route_id)
            if len(stops) < 2:
                continue

            rt  = gtfs_route.route_type
            cat = _TYPE_LABEL.get(rt, "Bus")

            if rt == 3:
                color = _BUS_COLOR
            elif rt == 0:
                color = _TRAM_COLOR
            else:
                color = _TYPE_COLOR.get(rt, _BUS_COLOR)

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
                        stop_id=stop_id, name=name,
                        lat=lat, lon=lon, base_demand=80.0,
                    )
                    # Stamp route_type on the station so the renderer draws
                    # the correct shape (square, diamond, circle) per transit mode
                    s.route_type = rt
                    stop_index[stop_id] = s
                entity.add_station(stop_index[stop_id])

            # Attach the best shape polyline so route lines follow road geometry
            sid = route_shape.get(gtfs_route.route_id)
            if sid and sid in shape_index:
                entity.shape_polyline = shape_index[sid]

            routes.append(entity)

        stations = list(stop_index.values())
        shaped   = sum(1 for r in routes if r.shape_polyline)
        log.info(f"Graph: {len(routes)} routes, {len(stations)} stations, "
                 f"{shaped} with shape data")
        return routes, stations, stop_index

    # _build_shape_index: Parse shape_points into sorted polylines keyed by shape_id.
    def _build_shape_index(self) -> Dict[str, List[Tuple[float, float]]]:
        raw: Dict[str, List[Tuple[int, float, float]]] = {}
        for sp in self._proc.feed.shape_points:
            raw.setdefault(sp.shape_id, []).append((sp.sequence, sp.lat, sp.lon))

        result = {}
        for shape_id, pts in raw.items():
            pts.sort(key=lambda x: x[0])
            result[shape_id] = [(lat, lon) for _, lat, lon in pts]

        log.debug(f"Shape index built: {len(result)} shapes")
        return result

    # _build_route_shape_map: Map route_id to the shape_id with the most points.
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
