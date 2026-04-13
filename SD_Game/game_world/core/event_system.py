# event_system: Deferred event queue for scheduling callbacks at a future simulation tick.

from collections import defaultdict
from typing import Callable
import logging

log = logging.getLogger(__name__)


# SimEvent: One scheduled callback with its target tick and keyword arguments.
class SimEvent:

    def __init__(self, tick: int, callback: Callable, **kwargs):
        self.tick     = tick
        self.callback = callback
        self.kwargs   = kwargs


# EventSystem: Fires queued callbacks at the right tick during the sim loop.
class EventSystem:

    def __init__(self):
        # Maps target tick to list of pending SimEvents
        self._queue: dict = defaultdict(list)

    # schedule: Enqueue a callback to fire at or after a given tick.
    def schedule(self, at_tick: int, callback: Callable, **kwargs):
        self._queue[at_tick].append(SimEvent(at_tick, callback, **kwargs))

    # process: Fire and remove all events due at or before current_tick.
    def process(self, current_tick: int):
        due = [t for t in self._queue if t <= current_tick]
        for t in due:
            for event in self._queue[t]:
                try:
                    event.callback(**event.kwargs)
                except Exception as e:
                    log.error(f"SimEvent error at tick {t}: {e}")
            del self._queue[t]

    # clear: Discard all pending events; called on simulation abort.
    def clear(self):
        self._queue.clear()
