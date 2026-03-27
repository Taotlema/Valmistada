"""
Filename: event_system.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""

# Libraries
from collections import defaultdict
from typing import Callable
import logging

log = logging.getLogger(__name__)


# SimEvent: One deferred action with a target tick and optional payload
class SimEvent:

    # __init__ (tick, callback, kwargs)
    def __init__(self, tick: int, callback: Callable, **kwargs):
        self.tick     = tick
        self.callback = callback
        self.kwargs   = kwargs


# EventSystem: Holds pending SimEvents and fires them when the clock reaches them
class EventSystem:

    def __init__(self):
        self._queue: dict = defaultdict(list)

    # schedule (at_tick, callback, **kwargs): Enqueue a future action
    def schedule(self, at_tick: int, callback: Callable, **kwargs):
        self._queue[at_tick].append(SimEvent(at_tick, callback, **kwargs))

    # process (current_tick): Fire and discard all events due at or before this tick
    def process(self, current_tick: int):
        due = [t for t in self._queue if t <= current_tick]
        for t in due:
            for event in self._queue[t]:
                try:
                    event.callback(**event.kwargs)
                except Exception as e:
                    log.error(f"SimEvent error at tick {t}: {e}")
            del self._queue[t]

    # clear: Wipe all pending events (called on simulation reset)
    def clear(self):
        self._queue.clear()