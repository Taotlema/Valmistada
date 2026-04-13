# map_loader: Converts geographic lat/lon coordinates to pixel positions on the map canvas.

from typing import Tuple
from data.processors.gtfs_processor import GTFSProcessor


# MapLoader: Linear projection bounded by GTFS stop extents; updates when canvas resizes.
class MapLoader:

    def __init__(self, processor: GTFSProcessor,
                 canvas_w: int = 800, canvas_h: int = 600, padding: int = 60):
        self._w   = canvas_w
        self._h   = canvas_h
        self._pad = padding

        min_lat, max_lat, min_lon, max_lon = processor.bounding_box()
        self._min_lat = min_lat
        self._max_lat = max_lat
        self._min_lon = min_lon
        self._max_lon = max_lon
        # Avoid division by zero on degenerate bounding boxes
        self._lat_rng = max(max_lat - min_lat, 1e-6)
        self._lon_rng = max(max_lon - min_lon, 1e-6)

    # to_pixel: Map (lat, lon) to (x, y) canvas pixels.
    # Longitude increases left-to-right; latitude is flipped so north is up.
    def to_pixel(self, lat: float, lon: float) -> Tuple[float, float]:
        usable_w = self._w - 2 * self._pad
        usable_h = self._h - 2 * self._pad
        x = self._pad + ((lon - self._min_lon) / self._lon_rng) * usable_w
        y = self._pad + ((self._max_lat - lat)  / self._lat_rng) * usable_h
        return (x, y)

    # update_canvas: Call whenever the canvas widget is resized.
    def update_canvas(self, w: int, h: int):
        self._w = w
        self._h = h
