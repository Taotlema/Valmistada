"""
Filename: gtfs_loader.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""

# Libraries
import os
import pandas as pd
import logging

# Modules
from data.models.gtfs_models import GTFSFeed, Stop, Route, Trip, StopTime, ShapePoint, ServiceCalendar

log = logging.getLogger(__name__)


# GTFSLoader: Parses a folder of GTFS .txt files into structured models
class GTFSLoader:

    # __init__ (gtfs_dir: path to folder containing .txt files)
    def __init__(self, gtfs_dir: str):
        self.gtfs_dir = gtfs_dir

    # _path (filename: basename): Resolve full file path
    def _path(self, filename: str) -> str:
        return os.path.join(self.gtfs_dir, filename)

    # _read (filename): Load a GTFS txt file as a DataFrame, return empty if missing
    def _read(self, filename: str) -> pd.DataFrame:
        fp = self._path(filename)
        if not os.path.exists(fp):
            log.warning(f"Missing GTFS file: {filename}")
            return pd.DataFrame()
        return pd.read_csv(fp, dtype=str, low_memory=False)

    # load (city: label for the feed): Parse all tables and return a GTFSFeed
    def load(self, city: str = "San Francisco") -> GTFSFeed:
        feed = GTFSFeed(agency_name="", city=city)

        # Agency
        ag = self._read("agency.txt")
        if not ag.empty:
            feed.agency_name = ag.iloc[0].get("agency_name", "Unknown")

        # Stops
        stops_df = self._read("stops.txt")
        if not stops_df.empty:
            for _, row in stops_df.iterrows():
                try:
                    feed.stops.append(Stop(
                        stop_id=row["stop_id"],
                        stop_name=row.get("stop_name", ""),
                        lat=float(row.get("stop_lat", 0)),
                        lon=float(row.get("stop_lon", 0)),
                    ))
                except (ValueError, KeyError):
                    continue

        # Routes
        routes_df = self._read("routes.txt")
        if not routes_df.empty:
            for _, row in routes_df.iterrows():
                try:
                    feed.routes.append(Route(
                        route_id=row["route_id"],
                        route_short_name=row.get("route_short_name", ""),
                        route_long_name=row.get("route_long_name", ""),
                        route_type=int(row.get("route_type", 3)),
                    ))
                except (ValueError, KeyError):
                    continue

        # Trips
        trips_df = self._read("trips.txt")
        if not trips_df.empty:
            for _, row in trips_df.iterrows():
                try:
                    feed.trips.append(Trip(
                        trip_id=row["trip_id"],
                        route_id=row["route_id"],
                        service_id=row["service_id"],
                        shape_id=row.get("shape_id"),
                        direction_id=int(row.get("direction_id", 0)),
                    ))
                except (ValueError, KeyError):
                    continue

        # Stop Times — only load a representative sample to stay memory-friendly
        st_df = self._read("stop_times.txt")
        if not st_df.empty:
            sample = st_df.sample(min(50_000, len(st_df)), random_state=42)
            for _, row in sample.iterrows():
                try:
                    feed.stop_times.append(StopTime(
                        trip_id=row["trip_id"],
                        stop_id=row["stop_id"],
                        stop_sequence=int(row.get("stop_sequence", 0)),
                        arrival_time=row.get("arrival_time", "00:00:00"),
                        departure_time=row.get("departure_time", "00:00:00"),
                    ))
                except (ValueError, KeyError):
                    continue

        # Shapes — sample for rendering
        shapes_df = self._read("shapes.txt")
        if not shapes_df.empty:
            for _, row in shapes_df.iterrows():
                try:
                    feed.shape_points.append(ShapePoint(
                        shape_id=row["shape_id"],
                        lat=float(row["shape_pt_lat"]),
                        lon=float(row["shape_pt_lon"]),
                        sequence=int(row["shape_pt_sequence"]),
                    ))
                except (ValueError, KeyError):
                    continue

        # Calendar
        cal_df = self._read("calendar.txt")
        if not cal_df.empty:
            for _, row in cal_df.iterrows():
                try:
                    feed.calendars.append(ServiceCalendar(
                        service_id=row["service_id"],
                        monday=row.get("monday", "0") == "1",
                        tuesday=row.get("tuesday", "0") == "1",
                        wednesday=row.get("wednesday", "0") == "1",
                        thursday=row.get("thursday", "0") == "1",
                        friday=row.get("friday", "0") == "1",
                        saturday=row.get("saturday", "0") == "1",
                        sunday=row.get("sunday", "0") == "1",
                        start_date=row.get("start_date", ""),
                        end_date=row.get("end_date", ""),
                    ))
                except (ValueError, KeyError):
                    continue

        log.info(f"Loaded GTFS for {city}: {len(feed.routes)} routes, "
                 f"{len(feed.stops)} stops, {len(feed.trips)} trips")
        return feed