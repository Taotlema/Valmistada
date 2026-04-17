# simulation_engine: QTimer-driven loop that builds the world, ticks entities, and fires completion events.

import os
import yaml
import logging
from typing import List

from PyQt6.QtCore import QTimer

from app_controller.event_bus import EventBus, Events
from app_controller.app import (GEN_DETERMINISTIC, GEN_HIGH_FIDELITY,
                                 GEN_RULE_BASED_V1, GEN_RULE_BASED_V2)

from game_world.core.time_manager  import TimeManager
from game_world.core.event_system  import EventSystem
from game_world.entities.route     import RouteEntity
from game_world.entities.station   import Station
from game_world.entities.vehicle   import Vehicle
from game_world.systems.scheduling_system import SchedulingSystem
from game_world.systems.modifier_system   import ModifierSystem
from game_world.map.graph_builder    import GraphBuilder
from game_world.map.map_loader       import MapLoader
from game_world.map.renderer_adapter import RendererAdapter
from data.processors.aggregator      import Aggregator

log = logging.getLogger(__name__)

# Timer fires every 100 ms at speed x1; faster speeds increase ticks-per-interval instead
_BASE_MS = 100


def _build_ridership_system(generation_model: str, sim_config: dict,
                             modifier_loader, aggregator: Aggregator):
    """Factory: return the correct RidershipSystem subclass for the selected model."""

    if generation_model == GEN_DETERMINISTIC:
        from game_world.systems.ridership_system_deterministic import RidershipSystem
    elif generation_model == GEN_HIGH_FIDELITY:
        from game_world.systems.ridership_system_hifi import RidershipSystem
    elif generation_model == GEN_RULE_BASED_V2:
        from game_world.systems.ridership_system_rb2 import RidershipSystem
    else:
        # Default / GEN_RULE_BASED_V1
        from game_world.systems.ridership_system import RidershipSystem

    return RidershipSystem(sim_config, modifier_loader, aggregator)


# SimulationEngine: Owns the QTimer loop, all entity lists, and the rendering pipeline.
class SimulationEngine:

    def __init__(self, bus: EventBus, app_controller,
                 sim_config_path: str, trial_number: int):
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
        self._ridership:  object          = None
        self._scheduling: SchedulingSystem = None

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)

        # Wire calendar boundary callbacks
        self._time.on_new_day   = self._on_new_day
        self._time.on_new_month = self._on_new_month
        self._time.on_year_end  = self._on_year_end

        self._running = False
        log.info(f"SimulationEngine created - trial {trial_number}")

    # build_world: Construct all entities from a loaded city processor.
    def build_world(self, city_label: str, canvas_w: int = 800, canvas_h: int = 600):
        proc = self._ctrl.processors.get(city_label)
        if not proc:
            log.error(f"No processor found for {city_label}")
            return

        # Respect the full_routes toggle set on AppController
        max_routes = self._ctrl.max_routes_cap()
        builder = GraphBuilder(proc, max_routes=max_routes)
        self.routes, self.stations, _ = builder.build()

        self.map_loader = MapLoader(proc, canvas_w, canvas_h)
        self.renderer   = RendererAdapter(self.map_loader)

        # Apply population and land-use demand weights before spawning vehicles
        mod = self._ctrl.modifier
        if self._ctrl.modifier_enabled():
            ModifierSystem(mod).apply(self.stations)

        # Instantiate the correct ridership system for the selected generation model
        generation_model = getattr(self._ctrl, "generation_model", GEN_RULE_BASED_V1)
        self._ridership = _build_ridership_system(
            generation_model, self._cfg, mod, self._aggreg
        )
        log.info(f"Ridership system: {generation_model} | routes: {len(self.routes)} "
                 f"(full_routes={self._ctrl.full_routes})")

        self._scheduling = SchedulingSystem(
            self._cfg, capacity=self._cfg["simulation"]["vehicle_capacity"]
        )
        self._scheduling.initialise(self.routes)
        self.vehicles = self._scheduling.all_vehicles()

        log.info(f"World built: {len(self.routes)} routes, {len(self.vehicles)} vehicles")

    # start: Begin the QTimer tick loop.
    def start(self):
        if self._running:
            return
        self._running = True
        self._timer.start(self._interval_ms())
        self.bus.publish(Events.SIM_STARTED)

    # pause: Freeze the loop without clearing simulation state.
    def pause(self):
        if not self._running:
            return
        self._running = False
        self._timer.stop()
        self.bus.publish(Events.SIM_PAUSED)

    # resume: Restart the loop from where it paused.
    def resume(self):
        if self._running:
            return
        self._running = True
        self._timer.start(self._interval_ms())
        self.bus.publish(Events.SIM_RESUMED)

    # abort: Stop the loop and discard all in-progress data.
    def abort(self):
        self._timer.stop()
        self._running = False
        self._aggreg  = Aggregator()
        self._events.clear()
        self.bus.publish(Events.SIM_ABORTED)

    # set_speed: Change the speed multiplier by index into the speed_levels list.
    def set_speed(self, level_index: int):
        self._speed_idx = max(0, min(level_index, len(self._speed_levels) - 1))
        if self._running:
            self._timer.setInterval(self._interval_ms())
        self.bus.publish(Events.SIM_SPEED_CHANGED, self.current_speed())

    # current_speed: Return the active speed multiplier integer.
    def current_speed(self) -> int:
        return self._speed_levels[self._speed_idx]

    # is_running: True while the QTimer loop is active.
    def is_running(self) -> bool:
        return self._running

    # date_label: Current sim date as a human-readable string.
    def date_label(self) -> str:
        return self._time.current_date_label()

    # progress: Year fraction completed, 0.0 to 1.0.
    def progress(self) -> float:
        return self._time.progress()

    # _tick: Core loop body called by QTimer; advances time and updates all entities.
    def _tick(self):
        if not self._running:
            return

        speed = self.current_speed()
        dt    = 1.0 / self._ticks_per_day

        # Run multiple sim steps per real-time tick for higher speed levels
        for _ in range(speed):
            self._time.advance()
            self._events.process(self._time._total_ticks)

            for s in self.stations:
                s.update(self._time._total_ticks, dt)

            self._scheduling.update(self.routes, self._time.hour_of_day())
            self.vehicles = self._scheduling.all_vehicles()

            for v in self.vehicles:
                v.update(self._time._total_ticks, dt)

        # Publish engine reference so UI can read date, progress, and stats
        self.bus.publish(Events.SIM_TICK, self)

    # _on_new_day: Record ridership for the day that just finished.
    def _on_new_day(self, date):
        self._ridership.process_day(
            routes=self.routes,
            month_label=self._time.current_month_label(),
            day_type=self._time.day_type(),
            month_int=date.month,
            hour=12.0,
        )

    # _on_new_month: Log the month transition for monitoring.
    def _on_new_month(self, date):
        log.info(f"Month transition to {date.strftime('%B %Y')}")

    # _on_year_end: Flush the aggregator and fire the completion event.
    def _on_year_end(self):
        self._timer.stop()
        self._running = False
        city   = list(self._ctrl.feeds.keys())[0]
        result = self._aggreg.flush(self.trial_number, city=city)
        self.bus.publish(Events.SIM_COMPLETED, result)
        log.info("Year complete.")

    # _interval_ms: Calculate the QTimer interval for the current speed level.
    def _interval_ms(self) -> int:
        return max(16, _BASE_MS // self.current_speed())
