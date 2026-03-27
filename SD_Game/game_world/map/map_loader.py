"""
Filename: map_loader.py
Author: Ayemhenre Isikhuemhen
Description: Resolves geo-coordinates to pixel positions for the map canvas
             using a simple linear projection within the GTFS bounding box.
Last Updated: March, 2026
"""

# Libraries
from typing import Tuple

# Modules
from data.processors.gtfs_processor import GTFSProcessor


# MapLoader: Owns the lat/lon ↔ pixel coordinate transform
class MapLoader:

    # __init__ (processor, canvas_w, canvas_h, padding)
    def __init__(self, processor: GTFSProcessor,
                 canvas_w: int = 800, canvas_h: int = 600, padding: int = 30):
        self._w   = canvas_w
        self._h   = canvas_h
        self._pad = padding
        min_lat, max_lat, min_lon, max_lon = processor.bounding_box()
        self._min_lat = min_lat
        self._max_lat = max_lat
        self._min_lon = min_lon
        self._max_lon = max_lon
        self._lat_rng = max(max_lat - min_lat, 1e-6)
        self._lon_rng = max(max_lon - min_lon, 1e-6)

    # to_pixel (lat, lon): Convert geographic coords to (x, y) canvas pixels
    def to_pixel(self, lat: float, lon: float) -> Tuple[float, float]:
        usable_w = self._w - 2 * self._pad
        usable_h = self._h - 2 * self._pad
        x = self._pad + ((lon - self._min_lon) / self._lon_rng) * usable_w
        y = self._pad + ((self._max_lat - lat) / self._lat_rng) * usable_h
        return (x, y)

    # update_canvas (w, h): Call when the widget is resized
    def update_canvas(self, w: int, h: int):
        self._w = w
        self._h = h