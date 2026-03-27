"""
Filename: simulation_engine.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""

# Libraries
import yaml
import logging
from typing import List

from PyQt6.QtCore import QTimer

# Modules
from app_controller.event_bus import EventBus, Events
from game_world.core.time_manager import TimeManager
from game_world.core.event_system import EventSystem
from game_world.entities.route import RouteEntity
from game_world.entities.station import Station
from game_world.entities.vehicle import Vehicle
from game_world.systems.ridership_system import RidershipSystem
from game_world.systems.scheduling_system import SchedulingSystem
from game_world.systems.modifier_system import ModifierSystem
from game_world.map.graph_builder import GraphBuilder
from game_world.map.map_loader import MapLoader
from game_world.map.renderer_adapter import RendererAdapter
from data.processors.aggregator import Aggregator

log = logging.getLogger(__name__)

_BASE_INTERVAL_MS = 100


# SimulationEngine: Single-session sim loop driven by a QTimer
class SimulationEngine:

    # __init__ (bus, app_controller, sim_config_path, trial_number)
    def __init__(self, bus: EventBus, app_controller, sim_config_path: str,
                 trial_number: int):
        self.bus          = bus
        self._ctrl        = app_controller
        self.trial_number = trial_number

        with open(sim_config_path, "r") as f:
            self._cfg = yaml.safe_load(f)

        sc = self._cfg["simulation"]
        self._speed_levels  = sc["speed_levels"]
        self._speed_idx     = sc["speed_levels"].index(sc["default_speed"])
        self._ticks_per_day = sc["ticks_per_day"]

        self._time   = TimeManager(sc["sim_year"], self._ticks_per_day)
        self._events = EventSystem()
        self._aggreg = Aggregator()

        self.routes:   List[RouteEntity] = []
        self.stations: List[Station]     = []
        self.vehicles: List[Vehicle]     = []

        self.map_loader: MapLoader       = None
        self.renderer:   RendererAdapter = None

        self._ridership:  RidershipSystem  = None
        self._scheduling: SchedulingSystem = None

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)

        self._time.on_new_day   = self._on_new_day
        self._time.on_new_month = self._on_new_month
        self._time.on_year_end  = self._on_year_end

        self._running = False
        log.info(f"SimulationEngine created — trial {trial_number}")

    # build_world (city_label): Construct entity graph from the loaded processor
    def build_world(self, city_label: str, canvas_w: int = 800, canvas_h: int = 600):
        proc = self._ctrl.processors.get(city_label)
        if not proc:
            log.error(f"No processor found for {city_label}")
            return

        builder = GraphBuilder(proc, max_routes=40)
        self.routes, self.stations, _idx = builder.build()

        self.map_loader = MapLoader(proc, canvas_w, canvas_h)
        self.renderer   = RendererAdapter(self.map_loader)

        mod = self._ctrl.modifier
        ModifierSystem(mod).apply(self.stations)

        self._ridership  = RidershipSystem(self._cfg, mod, self._aggreg)
        self._scheduling = SchedulingSystem(
            self._cfg, capacity=self._cfg["simulation"]["vehicle_capacity"]
        )
        self._scheduling.initialise(self.routes)
        self.vehicles = self._scheduling.all_vehicles()

        log.info(f"World built for {city_label}: "
                 f"{len(self.routes)} routes, {len(self.vehicles)} initial vehicles")

    # start: Begin the tick loop
    def start(self):
        if self._running:
            return
        self._running = True
        self._timer.start(self._interval_ms())
        self.bus.publish(Events.SIM_STARTED)

    # pause: Freeze the tick loop without resetting state
    def pause(self):
        if not self._running:
            return
        self._running = False
        self._timer.stop()
        self.bus.publish(Events.SIM_PAUSED)

    # resume
    def resume(self):
        self.start()
        self.bus.publish(Events.SIM_RESUMED)

    # abort: Stop and discard all in-progress data
    def abort(self):
        self._timer.stop()
        self._running = False
        self._aggreg  = Aggregator()
        self._events.clear()
        self.bus.publish(Events.SIM_ABORTED)

    # set_speed (level_index): Change simulation speed multiplier
    def set_speed(self, level_index: int):
        self._speed_idx = max(0, min(level_index, len(self._speed_levels) - 1))
        if self._running:
            self._timer.setInterval(self._interval_ms())
        self.bus.publish(Events.SIM_SPEED_CHANGED, self.current_speed())

    # current_speed: Return the active speed multiplier
    def current_speed(self) -> int:
        return self._speed_levels[self._speed_idx]

    # is_running
    def is_running(self) -> bool:
        return self._running

    # date_label: Passthrough to TimeManager
    def date_label(self) -> str:
        return self._time.current_date_label()

    # progress: 0.0–1.0 year fraction complete
    def progress(self) -> float:
        return self._time.progress()

    # _tick: Core loop — called by QTimer each interval
    def _tick(self):
        if not self._running:
            return

        speed = self.current_speed()
        for _ in range(speed):
            self._time.advance()
            self._events.process(self._time._total_ticks)

            dt = 1.0 / self._ticks_per_day
            for s in self.stations:
                s.update(self._time._total_ticks, dt)

            self._scheduling.update(self.routes, self._time.hour_of_day())
            self.vehicles = self._scheduling.all_vehicles()

            for v in self.vehicles:
                v.update(self._time._total_ticks, dt)

        self.bus.publish(Events.SIM_TICK, self)

    # _on_new_day (date): Tally ridership for the completed day
    def _on_new_day(self, date):
        self._ridership.process_day(
            routes=self.routes,
            month_label=self._time.current_month_label(),
            day_type=self._time.day_type(),
            month_int=date.month,
            hour=12.0,
        )

    # _on_new_month (date): Log month transition
    def _on_new_month(self, date):
        log.info(f"Sim month → {date.strftime('%B %Y')}")

    # _on_year_end: Flush results and fire completion event
    def _on_year_end(self):
        self._timer.stop()
        self._running = False
        result = self._aggreg.flush(
            self.trial_number, city=list(self._ctrl.feeds.keys())[0]
        )
        self.bus.publish(Events.SIM_COMPLETED, result)
        log.info("Simulation year complete.")

    # _interval_ms: Timer interval for the current speed level
    def _interval_ms(self) -> int:
        return max(16, _BASE_INTERVAL_MS // self.current_speed())