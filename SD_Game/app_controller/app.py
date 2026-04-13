# app: Central controller that wires loaders, screens, and event bus into one runtime object.

import os
import logging

from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QTimer

from app_controller.event_bus import EventBus, Events
from app_controller.screen_manager import ScreenManager

from data.loaders.gtfs_loader import GTFSLoader
from data.loaders.modifier_loader import ModifierLoader
from data.loaders.output_loader import OutputLoader
from data.processors.gtfs_processor import GTFSProcessor
from data.processors.data_validator import DataValidator
from data.storage.file_manager import FileManager

log = logging.getLogger(__name__)


# AppController: Top-level QMainWindow that owns all shared application state.
class AppController(QMainWindow):

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self.bus = EventBus()

        # Resolve data paths from settings.yaml
        self.gtfs_root     = settings["paths"]["gtfs_data"]
        self.modifier_root = settings["paths"]["modifier_data"]
        self.output_root   = settings["paths"]["output"]
        self.assets_root   = settings["paths"]["assets"]

        FileManager.ensure_dir(self.output_root)

        self.feeds:      dict = {}
        self.processors: dict = {}

        # Load modifier data at startup so it is ready when the sim runs
        self.modifier = ModifierLoader(
            os.path.join(self.modifier_root, "San Francisco")
        )
        self.modifier.load()

        self.sim_engine = None

        self._build_ui()
        self._connect_events()
        self._start_loading()

    # _build_ui: Instantiate all six screens and register them with ScreenManager.
    def _build_ui(self):
        from ui.screens.loading_screen    import LoadingScreen
        from ui.screens.start_screen      import StartScreen
        from ui.screens.input_screen      import InputScreen
        from ui.screens.output_screen     import OutputScreen
        from ui.screens.dictionary_screen import DictionaryScreen
        from ui.screens.game_world_screen import GameWorldScreen

        self.screen_manager = ScreenManager(self.bus)

        self.loading_screen    = LoadingScreen(self.bus, self.settings)
        self.start_screen      = StartScreen(self.bus, self.settings, self)
        self.input_screen      = InputScreen(self.bus, self.settings, self)
        self.output_screen     = OutputScreen(self.bus, self.settings, self)
        self.dictionary_screen = DictionaryScreen(self.bus, self.settings, self.assets_root)
        self.game_world_screen = GameWorldScreen(self.bus, self.settings, self)

        sm = self.screen_manager
        sm.register(ScreenManager.LOADING,    self.loading_screen)
        sm.register(ScreenManager.START,      self.start_screen)
        sm.register(ScreenManager.INPUT,      self.input_screen)
        sm.register(ScreenManager.OUTPUT,     self.output_screen)
        sm.register(ScreenManager.DICTIONARY, self.dictionary_screen)
        sm.register(ScreenManager.GAME_WORLD, self.game_world_screen)

        self.setCentralWidget(self.screen_manager)
        cfg = self.settings["app"]
        self.setWindowTitle(cfg["title"])
        self.resize(cfg["window_width"], cfg["window_height"])

    # _connect_events: Wire bus events to controller-level handlers.
    def _connect_events(self):
        self.bus.subscribe(Events.SIM_COMPLETED, self._on_sim_completed)
        self.bus.subscribe(Events.SIM_ABORTED,   self._on_sim_aborted)

    # _start_loading: Show the loading splash then advance to start after a delay.
    def _start_loading(self):
        self.screen_manager.navigate(ScreenManager.LOADING)
        duration = self.settings["app"].get("loading_duration_ms", 2500)
        QTimer.singleShot(duration, self._finish_loading)

    # _finish_loading: Stop the loading animation and switch to the start screen.
    def _finish_loading(self):
        self.loading_screen.stop_animation()
        self.screen_manager.navigate(ScreenManager.START)

    # load_city_feed: Validate, parse, and index a GTFS feed on demand.
    def load_city_feed(self, city_label: str, gtfs_dir: str):
        valid, missing = DataValidator.validate_gtfs_dir(gtfs_dir)
        if not valid:
            log.warning(f"GTFS incomplete for {city_label}: missing {missing}")
            return
        loader = GTFSLoader(gtfs_dir)
        feed   = loader.load(city=city_label)
        proc   = GTFSProcessor(feed)
        self.feeds[city_label]      = feed
        self.processors[city_label] = proc
        self.bus.publish(Events.GTFS_LOADED, city_label)
        log.info(f"Feed ready: {city_label}")

    # is_batch_ready: True if at least one city feed has been loaded.
    def is_batch_ready(self) -> bool:
        return len(self.feeds) > 0

    # is_modifier_ready: True if historical ridership data was found and loaded.
    def is_modifier_ready(self) -> bool:
        return not self.modifier.ridership_df.empty

    # next_trial_number: Return the next unused trial integer from the output folder.
    def next_trial_number(self) -> int:
        return FileManager.next_trial_number(self.output_root)

    # _on_sim_completed: Export results to disk and notify the output screen.
    def _on_sim_completed(self, trial_result):
        from data.storage.export_manager import ExportManager
        ExportManager(self.output_root).export(trial_result)
        self.output_screen.refresh()
        self.bus.publish(Events.TRIAL_SAVED, trial_result.trial_number)

    # _on_sim_aborted: Nothing to save when the user cancels early.
    def _on_sim_aborted(self):
        log.info("Simulation aborted - no data saved.")
