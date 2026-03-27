"""
Filename: graph_builder.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""

"""
Filename: graph_builder.py
Author: Ayemhenre Isikhuemhen
Description: Converts a GTFSProcessor into a network of RouteEntity and Station
             objects ready for the simulation engine to operate on.
Last Updated: March, 2026
"""

# Libraries
from typing import Dict, List, Tuple
import logging

# Modules
from data.processors.gtfs_processor import GTFSProcessor
from game_world.entities.route import RouteEntity
from game_world.entities.station import Station

log = logging.getLogger(__name__)

_TYPE_LABEL = {0: "Tram/Light Rail", 1: "Subway", 3: "Bus", 5: "Cable Car"}
_TYPE_COLOR = {
    0: (255, 193,  7),
    1: (233,  30, 99),
    3: ( 66, 165, 245),
    5: (156,  39, 176),
}


# GraphBuilder: Produces the entity graph from processed GTFS data
class GraphBuilder:

    # __init__ (processor, max_routes: cap for rendering performance)
    def __init__(self, processor: GTFSProcessor, max_routes: int = 40):
        self._proc       = processor
        self._max_routes = max_routes

    # build: Return (routes, stations, stop_index) entity collections
    def build(self) -> Tuple[List[RouteEntity], List[Station], Dict[str, Station]]:
        stop_index: Dict[str, Station] = {}
        routes: List[RouteEntity]      = []

        gtfs_routes = self._proc.feed.routes[:self._max_routes]

        for gtfs_route in gtfs_routes:
            stops = self._proc.get_route_stops(gtfs_route.route_id)
            if len(stops) < 2:
                continue

            cat = _TYPE_LABEL.get(gtfs_route.route_type, "Bus")
            re  = RouteEntity(
                route_id=gtfs_route.route_id,
                short_name=gtfs_route.route_short_name,
                long_name=gtfs_route.route_long_name,
                route_type=gtfs_route.route_type,
                service_category=cat,
            )
            re.color = _TYPE_COLOR.get(gtfs_route.route_type, (66, 165, 245))

            for (stop_id, lat, lon) in stops:
                if stop_id not in stop_index:
                    gtfs_stop = self._proc.stop_index.get(stop_id)
                    name = gtfs_stop.stop_name if gtfs_stop else stop_id
                    stop_index[stop_id] = Station(
                        stop_id=stop_id, name=name,
                        lat=lat, lon=lon, base_demand=80.0
                    )
                re.add_station(stop_index[stop_id])

            routes.append(re)

        stations = list(stop_index.values())
        log.info(f"Graph built: {len(routes)} routes, {len(stations)} stations")
        return routes, stations, stop_index