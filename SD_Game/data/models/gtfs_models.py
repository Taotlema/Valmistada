"""
Filename: gtfs_models.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""

# Libraries
from dataclasses import dataclass, field
from typing import List, Optional


# Stop: One physical boarding/alighting point
@dataclass
class Stop:
    stop_id: str
    stop_name: str
    lat: float
    lon: float


# Route: A named transit service line
@dataclass
class Route:
    route_id: str
    route_short_name: str
    route_long_name: str
    route_type: int             # 0=Tram, 1=Metro, 3=Bus, 5=CableCar


# Trip: A single scheduled run of a route on a service day
@dataclass
class Trip:
    trip_id: str
    route_id: str
    service_id: str
    shape_id: Optional[str] = None
    direction_id: int = 0


# StopTime: Scheduled arrival/departure for one stop within a trip
@dataclass
class StopTime:
    trip_id: str
    stop_id: str
    stop_sequence: int
    arrival_time: str           # "HH:MM:SS" — may exceed 24h in GTFS
    departure_time: str


# Shape: Ordered lat/lon points tracing a route's drawn path
@dataclass
class ShapePoint:
    shape_id: str
    lat: float
    lon: float
    sequence: int


# ServiceCalendar: Weekly service availability for a service_id
@dataclass
class ServiceCalendar:
    service_id: str
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool
    start_date: str
    end_date: str


# GTFSFeed: Top-level container aggregating all parsed GTFS tables
@dataclass
class GTFSFeed:
    agency_name: str
    city: str
    stops: List[Stop] = field(default_factory=list)
    routes: List[Route] = field(default_factory=list)
    trips: List[Trip] = field(default_factory=list)
    stop_times: List[StopTime] = field(default_factory=list)
    shape_points: List[ShapePoint] = field(default_factory=list)
    calendars: List[ServiceCalendar] = field(default_factory=list)