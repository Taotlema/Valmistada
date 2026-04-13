# renderer_adapter: Draws route lines, station markers, vehicle worms, and the legend.
#
# Drawing order:
#   1. Faint green pixel grid for the retro CRT texture
#   2. Route lines using shape polylines when available; two passes (glow + colour)
#   3. Station markers sized and shaped by transit mode
#   4. Vehicle worms following the shape polyline between stops
#   5. Legend overlay in the bottom-left corner

import math
from typing import List, Tuple

from PyQt6.QtGui  import (QPainter, QColor, QPen, QBrush,
                           QFont, QPainterPath)
from PyQt6.QtCore import Qt, QPointF, QRectF

from game_world.entities.route   import RouteEntity
from game_world.entities.station import Station
from game_world.entities.vehicle import Vehicle
from game_world.map.map_loader   import MapLoader

# Station fill colours by GTFS route_type
_S_BUS   = QColor(255, 255, 255)
_S_TRAM  = QColor(255, 255, 255)
_S_CABLE = QColor(255, 255, 255)
_S_METRO = QColor(210, 255, 255)

# Legend entries pair a colour with a display label
_LEGEND = [
    (_S_BUS,   "  BUS STOP"),
    (_S_TRAM,  "  TRAM STOP"),
    (_S_CABLE, "  CABLE CAR"),
    (_S_METRO, "  METRO STN"),
]


# RendererAdapter: Translates simulation entity state into QPainter draw calls each frame.
class RendererAdapter:

    def __init__(self, map_loader: MapLoader):
        self._map = map_loader

    # _project_stations: Cache pixel coords on every station before drawing.
    def _project_stations(self, stations: List[Station]):
        for s in stations:
            s.x_px, s.y_px = self._map.to_pixel(s.lat, s.lon)

    # _shape_pixel_pts: Convert a (lat, lon) polyline to pixel QPointFs.
    def _shape_pixel_pts(self, polyline: List[Tuple[float, float]]) -> List[QPointF]:
        return [QPointF(*self._map.to_pixel(lat, lon)) for lat, lon in polyline]

    # _project_vehicle: Walk the shape polyline arc-length to place the vehicle at fraction p.
    # Falls back to a straight station-to-station line when no shape is available.
    def _project_vehicle(self, v: Vehicle):
        cs    = v.current_station
        ns    = v.next_station
        p     = v.progress
        route = v.route

        if route.shape_polyline and len(route.shape_polyline) >= 2:
            shape_pts = self._shape_pixel_pts(route.shape_polyline)
            i_start   = self._nearest_shape_idx(shape_pts, cs.x_px, cs.y_px)
            i_end     = self._nearest_shape_idx(shape_pts, ns.x_px, ns.y_px)

            if i_start != i_end:
                if i_start > i_end:
                    i_start, i_end = i_end, i_start
                    p = 1.0 - p

                segment = shape_pts[i_start: i_end + 1]
                if len(segment) >= 2:
                    total = sum(
                        math.hypot(segment[k + 1].x() - segment[k].x(),
                                   segment[k + 1].y() - segment[k].y())
                        for k in range(len(segment) - 1)
                    )
                    if total > 0:
                        target = p * total
                        walked = 0.0
                        for k in range(len(segment) - 1):
                            a       = segment[k]
                            b       = segment[k + 1]
                            seg_len = math.hypot(b.x() - a.x(), b.y() - a.y())
                            if walked + seg_len >= target or k == len(segment) - 2:
                                frac   = (target - walked) / max(seg_len, 1e-6)
                                frac   = max(0.0, min(1.0, frac))
                                v.x_px = a.x() + (b.x() - a.x()) * frac
                                v.y_px = a.y() + (b.y() - a.y()) * frac
                                return
                            walked += seg_len

        # Straight-line fallback when shape data is unavailable
        v.x_px = cs.x_px + (ns.x_px - cs.x_px) * p
        v.y_px = cs.y_px + (ns.y_px - cs.y_px) * p

    # _nearest_shape_idx: Return the index of the shape point closest to (px, py).
    def _nearest_shape_idx(self, pts: List[QPointF], px: float, py: float) -> int:
        best_idx  = 0
        best_dist = float("inf")
        for i, pt in enumerate(pts):
            d = math.hypot(pt.x() - px, pt.y() - py)
            if d < best_dist:
                best_dist = d
                best_idx  = i
        return best_idx

    # render: Full draw pass for one simulation frame.
    def render(self, painter: QPainter,
               routes:   List[RouteEntity],
               stations: List[Station],
               vehicles: List[Vehicle],
               canvas_w: int, canvas_h: int):

        self._map.update_canvas(canvas_w, canvas_h)
        self._project_stations(stations)

        self._draw_grid(painter, canvas_w, canvas_h)
        self._draw_routes(painter, routes)
        self._draw_stations(painter, stations)
        self._draw_vehicles(painter, vehicles)

    # _draw_grid: Faint green CRT grid for the retro terminal feel.
    def _draw_grid(self, painter: QPainter, w: int, h: int):
        pen = QPen(QColor(0, 255, 136, 10))
        pen.setWidth(1)
        painter.setPen(pen)
        step = 24
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)

    # _draw_routes: Two-pass rendering; white glow underline then coloured overlay.
    def _draw_routes(self, painter: QPainter, routes: List[RouteEntity]):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for route in routes:
            if len(route.stations) < 2:
                continue

            # Prefer shape polyline for geographic accuracy; fall back to stop positions
            if route.shape_polyline and len(route.shape_polyline) >= 2:
                pts = [QPointF(*self._map.to_pixel(lat, lon))
                       for lat, lon in route.shape_polyline]
            else:
                pts = [QPointF(s.x_px, s.y_px) for s in route.stations]

            path = QPainterPath()
            path.moveTo(pts[0])
            for pt in pts[1:]:
                path.lineTo(pt)

            r, g, b = route.color

            # Pass 1: White glow for depth and contrast against the dark map
            pen_glow = QPen(QColor(255, 255, 255, 35))
            pen_glow.setWidthF(6.0)
            pen_glow.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen_glow.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.strokePath(path, pen_glow)

            # Pass 2: Coloured route line at full opacity
            pen_col = QPen(QColor(r, g, b, 210))
            pen_col.setWidthF(2.5)
            pen_col.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen_col.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.strokePath(path, pen_col)

    # _draw_stations: Different shape and size per GTFS route_type.
    def _draw_stations(self, painter: QPainter, stations: List[Station]):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for s in stations:
            rtype = getattr(s, "route_type", 3)

            if rtype == 1:
                # Metro: large red square with white outline for visibility
                sz = 8
                painter.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
                painter.setBrush(QBrush(_S_METRO))
                painter.drawRect(QRectF(s.x_px - sz / 2, s.y_px - sz / 2, sz, sz))

            elif rtype == 5:
                # Cable Car: circle with white outline
                painter.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
                painter.setBrush(QBrush(_S_CABLE))
                painter.drawEllipse(QPointF(s.x_px, s.y_px), 6, 6)

            elif rtype == 0:
                # Tram: amber diamond drawn as a 45-degree rotated square
                sz = 7
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(_S_TRAM))
                painter.save()
                painter.translate(s.x_px, s.y_px)
                painter.rotate(45)
                painter.drawRect(QRectF(-sz / 2, -sz / 2, sz, sz))
                painter.restore()

            else:
                # Bus: medium blue square
                sz = 6
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(_S_BUS))
                painter.drawRect(QRectF(s.x_px - sz / 2, s.y_px - sz / 2, sz, sz))

    # _draw_vehicles: Pixel worm; head square plus three shrinking tail segments.
    def _draw_vehicles(self, painter: QPainter, vehicles: List[Vehicle]):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)

        for v in vehicles:
            if not v.active:
                continue
            self._project_vehicle(v)

            rc, gc, bc = v.route.color

            # Tail direction based on the straight vector between stop positions
            cs  = v.current_station
            ns  = v.next_station
            dx  = ns.x_px - cs.x_px
            dy  = ns.y_px - cs.y_px
            mag = max(math.hypot(dx, dy), 1.0)
            ux, uy = dx / mag, dy / mag

            # Head: brightest, largest segment
            painter.setBrush(QBrush(QColor(rc, gc, bc, 245)))
            painter.drawRect(QRectF(v.x_px - 4, v.y_px - 4, 8, 8))

            # Tail: three segments fading in alpha and shrinking in size
            for seg in range(1, 4):
                tx    = v.x_px - ux * seg * 6
                ty    = v.y_px - uy * seg * 6
                alpha = max(50, 245 - seg * 65)
                size  = max(3, 7 - seg * 2)
                painter.setBrush(QBrush(QColor(rc, gc, bc, alpha)))
                painter.drawRect(QRectF(tx - size / 2, ty - size / 2, size, size))

    # _draw_legend: Semi-transparent bottom-
    """
    def _draw_legend(self, painter: QPainter, canvas_h: int):
        x0    = 14
        row_h = 22
        box_h = len(_LEGEND) * row_h + 12
        y0    = canvas_h - box_h - 14

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.drawRect(QRectF(x0 - 6, y0 - 6, 138, box_h + 10))

        font = QFont("Courier New", 9)
        font.setBold(True)
        painter.setFont(font)

        shapes = ["sq", "dia", "ci", "sq_lg"]

        for i, (color, label) in enumerate(_LEGEND):
            y     = y0 + i * row_h
            cy    = y + row_h // 2
            dot_x = x0 + 8

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))

            sh = shapes[i]
            if sh == "ci":
                painter.setPen(QPen(QColor(255, 255, 255, 180), 1.2))
                painter.drawEllipse(QPointF(dot_x, cy), 6, 6)
                painter.setPen(Qt.PenStyle.NoPen)
            elif sh == "dia":
                painter.save()
                painter.translate(dot_x, cy)
                painter.rotate(45)
                painter.drawRect(QRectF(-5, -5, 10, 10))
                painter.restore()
            elif sh == "sq_lg":
                painter.setPen(QPen(QColor(255, 255, 255, 180), 1.2))
                painter.drawRect(QRectF(dot_x - 6, cy - 6, 12, 12))
                painter.setPen(Qt.PenStyle.NoPen)
            else:
                painter.drawRect(QRectF(dot_x - 5, cy - 5, 10, 10))

            painter.setPen(QColor(200, 200, 200))
            painter.drawText(QPointF(dot_x + 16, cy + 4), label)
            painter.setPen(Qt.PenStyle.NoPen)
        """
