# gtfs_models: Dataclasses representing each parsed GTFS table.

from dataclasses import dataclass, field
from typing import List, Optional


# Stop: One physical boarding or alighting location with coordinates.
@dataclass
class Stop:
    stop_id:   str
    stop_name: str
    lat:       float
    lon:       float


# Route: A named transit line running between two termini with a fixed stop sequence.
@dataclass
class Route:
    route_id:         str
    route_short_name: str
    route_long_name:  str
    route_type:       int   # 0=Tram, 1=Subway, 3=Bus, 5=Cable Car


# Trip: A single scheduled run of a route on one service day.
@dataclass
class Trip:
    trip_id:      str
    route_id:     str
    service_id:   str
    shape_id:     Optional[str] = None
    direction_id: int = 0


# StopTime: One row of the stop_times table linking a trip to a stop with times.
@dataclass
class StopTime:
    trip_id:        str
    stop_id:        str
    stop_sequence:  int
    arrival_time:   str   # HH:MM:SS — may exceed 24h in GTFS
    departure_time: str


# ShapePoint: One lat/lon vertex in a GTFS shape polyline.
@dataclass
class ShapePoint:
    shape_id: str
    lat:      float
    lon:      float
    sequence: int


# ServiceCalendar: Days-of-week operating pattern for a service_id.
@dataclass
class ServiceCalendar:
    service_id: str
    monday:     bool
    tuesday:    bool
    wednesday:  bool
    thursday:   bool
    friday:     bool
    saturday:   bool
    sunday:     bool
    start_date: str
    end_date:   str


# GTFSFeed: Top-level container for all parsed GTFS tables from one city.
@dataclass
class GTFSFeed:
    agency_name:  str
    city:         str
    stops:        List[Stop]            = field(default_factory=list)
    routes:       List[Route]           = field(default_factory=list)
    trips:        List[Trip]            = field(default_factory=list)
    stop_times:   List[StopTime]        = field(default_factory=list)
    shape_points: List[ShapePoint]      = field(default_factory=list)
    calendars:    List[ServiceCalendar] = field(default_factory=list)
