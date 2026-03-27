"""
Filename: route.py
Author: Ayemhenre Isikhuemhen
Description: Route entity — ordered list of Station references and per-day boarding counters.
Last Updated: March, 2026
"""

# Libraries
from typing import List

# Modules
from game_world.entities.base_entity import BaseEntity
from game_world.entities.station import Station


# RouteEntity: One transit line with ordered stops and boarding counters
class RouteEntity(BaseEntity):

    # __init__ (route_id, short_name, long_name, route_type, service_category)
    def __init__(self, route_id: str, short_name: str, long_name: str,
                 route_type: int = 3, service_category: str = "Bus"):
        super().__init__(entity_id=route_id)
        self.short_name       = short_name
        self.long_name        = long_name
        self.route_type       = route_type
        self.service_category = service_category
        self.stations: List[Station] = []
        self.daily_boardings: int    = 0
        self.total_trips: int        = 0
        self.color: tuple = (66, 165, 245)

    # add_station (station): Append a stop to this route's sequence
    def add_station(self, station: Station):
        self.stations.append(station)

    # update (tick, dt): Nothing route-level per tick — vehicles do the work
    def update(self, tick: int, dt: float):
        pass

    # record_boarding (count): Accumulate boardings for the current sim day
    def record_boarding(self, count: int):
        self.daily_boardings += count

    # reset_day: Clear daily counter at the start of each new sim day
    def reset_day(self):
        self.daily_boardings = 0