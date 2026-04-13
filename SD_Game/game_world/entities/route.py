# route: Ordered list of Stations with daily boarding counters and a shape polyline.

from typing import List, Tuple, TYPE_CHECKING
from game_world.entities.base_entity import BaseEntity

if TYPE_CHECKING:
    from game_world.entities.station import Station


# RouteEntity: Represents one GTFS route with colour, stops, and optional shape geometry.
class RouteEntity(BaseEntity):

    def __init__(self, route_id: str, short_name: str, long_name: str,
                 route_type: int = 3, service_category: str = "Bus"):
        super().__init__(entity_id=route_id)
        self.short_name:       str                           = short_name
        self.long_name:        str                           = long_name
        self.route_type:       int                           = route_type
        self.service_category: str                           = service_category
        self.stations:         List["Station"]               = []
        self.daily_boardings:  int                           = 0
        self.total_trips:      int                           = 0
        self.color:            tuple                         = (66, 165, 245)
        # Shape polyline is a list of (lat, lon) tuples from shapes.txt
        # Used by the renderer to draw smooth geographic paths
        self.shape_polyline:   List[Tuple[float, float]]     = []

    # update: Nothing to do at the route level; vehicles handle all movement.
    def update(self, tick: int, dt: float):
        pass

    # add_station: Append a stop to this route's ordered sequence.
    def add_station(self, station: "Station"):
        self.stations.append(station)

    # record_boarding: Add to the running daily boarding total.
    def record_boarding(self, count: int):
        self.daily_boardings += count

    # reset_day: Clear the daily counter at the start of each new sim day.
    def reset_day(self):
        self.daily_boardings = 0
