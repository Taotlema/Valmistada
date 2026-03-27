"""
Filename: renderer_adapter.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""

"""
Filename: renderer_adapter.py
Author: Ayemhenre Isikhuemhen
Description: Translates simulation entity state into QPainter draw calls,
             rendering stations, route lines, and animated vehicles on a canvas.
Last Updated: March, 2026
"""

# Libraries
from typing import List

from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QPointF

# Modules
from game_world.entities.route import RouteEntity
from game_world.entities.station import Station
from game_world.entities.vehicle import Vehicle
from game_world.map.map_loader import MapLoader


# RendererAdapter: Stateless draw helper — call render() every paint event
class RendererAdapter:

    STATION_RADIUS = 3
    VEHICLE_LEN    = 10

    # __init__ (map_loader)
    def __init__(self, map_loader: MapLoader):
        self._map = map_loader

    # _project_stations: Cache pixel coords on each station
    def _project_stations(self, stations: List[Station]):
        for s in stations:
            s.x_px, s.y_px = self._map.to_pixel(s.lat, s.lon)

    # _project_vehicle: Interpolate vehicle pixel position between stops
    def _project_vehicle(self, v: Vehicle):
        cs    = v.current_station
        ns    = v.next_station
        p     = v.progress
        v.x_px = cs.x_px + (ns.x_px - cs.x_px) * p
        v.y_px = cs.y_px + (ns.y_px - cs.y_px) * p

    # render (painter, routes, stations, vehicles, canvas_w, canvas_h)
    def render(self, painter: QPainter,
               routes: List[RouteEntity],
               stations: List[Station],
               vehicles: List[Vehicle],
               canvas_w: int, canvas_h: int):

        self._map.update_canvas(canvas_w, canvas_h)
        self._project_stations(stations)

        # Route lines
        for route in routes:
            if len(route.stations) < 2:
                continue
            r, g, b = route.color
            pen = QPen(QColor(r, g, b, 160))
            pen.setWidth(2)
            painter.setPen(pen)
            for i in range(len(route.stations) - 1):
                a  = route.stations[i]
                b_ = route.stations[i + 1]
                painter.drawLine(QPointF(a.x_px, a.y_px), QPointF(b_.x_px, b_.y_px))

        # Stations
        painter.setPen(QPen(QColor(200, 200, 200, 200)))
        painter.setBrush(QBrush(QColor(240, 240, 240, 220)))
        r = self.STATION_RADIUS
        for s in stations:
            painter.drawEllipse(QPointF(s.x_px, s.y_px), r, r)

        # Vehicles — worm body
        for v in vehicles:
            if not v.active:
                continue
            self._project_vehicle(v)
            cs = v.current_station
            ns = v.next_station
            dx = ns.x_px - cs.x_px
            dy = ns.y_px - cs.y_px
            length = max((dx**2 + dy**2) ** 0.5, 1.0)
            ux, uy = dx / length, dy / length

            rc, gc, bc = v.route.color
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(rc, gc, bc, 230)))
            painter.drawEllipse(QPointF(v.x_px, v.y_px), 5, 5)

            for seg in range(1, 4):
                tx    = v.x_px - ux * seg * (self.VEHICLE_LEN / 3)
                ty    = v.y_px - uy * seg * (self.VEHICLE_LEN / 3)
                alpha = max(60, 230 - seg * 55)
                size  = max(2, 5 - seg)
                painter.setBrush(QBrush(QColor(rc, gc, bc, alpha)))
                painter.drawEllipse(QPointF(tx, ty), size, size)