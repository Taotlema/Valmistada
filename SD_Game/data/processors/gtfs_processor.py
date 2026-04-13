# gtfs_processor: Indexes a GTFSFeed into fast lookup structures for the simulation.

from typing import Dict, List, Tuple
import logging

from data.models.gtfs_models import GTFSFeed, Stop, Route, Trip

log = logging.getLogger(__name__)


# GTFSProcessor: Builds stop, route, and trip indexes and derives ordered stop sequences.
class GTFSProcessor:

    def __init__(self, feed: GTFSFeed):
        self.feed = feed
        self.stop_index:   Dict[str, Stop]  = {s.stop_id:  s for s in feed.stops}
        self.route_index:  Dict[str, Route] = {r.route_id: r for r in feed.routes}
        self.trip_index:   Dict[str, Trip]  = {t.trip_id:  t for t in feed.trips}
        self._route_stops: Dict[str, List[Tuple[str, float, float]]] = {}
        self._build_route_stops()
        log.info(f"GTFSProcessor ready: {len(self.stop_index)} stops, "
                 f"{len(self.route_index)} routes")

    # _build_route_stops: Derive ordered stop sequences per route from stop_times.
    def _build_route_stops(self):
        trip_to_route: Dict[str, str] = {
            t.trip_id: t.route_id for t in self.feed.trips
        }

        # Group stop sequences by route then by trip
        route_trip_stops: Dict[str, Dict[str, List[Tuple[int, str]]]] = {}
        for st in self.feed.stop_times:
            route_id = trip_to_route.get(st.trip_id)
            if route_id is None:
                continue
            route_trip_stops.setdefault(route_id, {})
            route_trip_stops[route_id].setdefault(st.trip_id, [])
            route_trip_stops[route_id][st.trip_id].append(
                (st.stop_sequence, st.stop_id)
            )

        # Pick the longest trip as the canonical sequence for each route
        for route_id, trips in route_trip_stops.items():
            best    = max(trips, key=lambda t: len(trips[t]))
            ordered = sorted(trips[best], key=lambda x: x[0])
            stops_out = []
            seen: set = set()
            for _seq, stop_id in ordered:
                if stop_id in seen:
                    continue
                seen.add(stop_id)
                stop = self.stop_index.get(stop_id)
                if stop:
                    stops_out.append((stop_id, stop.lat, stop.lon))
            if len(stops_out) >= 2:
                self._route_stops[route_id] = stops_out

    # get_route_stops: Return ordered (stop_id, lat, lon) tuples for a route.
    def get_route_stops(self, route_id: str) -> List[Tuple[str, float, float]]:
        return self._route_stops.get(route_id, [])

    # bounding_box: Return (min_lat, max_lat, min_lon, max_lon) across all stops.
    def bounding_box(self) -> Tuple[float, float, float, float]:
        if not self.feed.stops:
            return (37.70, 37.83, -122.52, -122.36)
        lats = [s.lat for s in self.feed.stops]
        lons = [s.lon for s in self.feed.stops]
        return (min(lats), max(lats), min(lons), max(lons))

    # service_category: Human label for a GTFS route_type integer.
    @staticmethod
    def service_category(route_type: int) -> str:
        return {
            0: "Tram/Light Rail",
            1: "Subway",
            3: "Bus",
            5: "Cable Car",
        }.get(route_type, "Bus")
