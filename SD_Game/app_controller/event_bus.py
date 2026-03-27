"""
Filename: event_bus.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""
# Libraries
from collections import defaultdict
from typing import Callable, Any
import logging

log = logging.getLogger(__name__)


# EventBus: Global singleton-style pub/sub dispatcher
class EventBus:

    def __init__(self):
        # topic → list of subscriber callbacks
        self._subscribers: dict = defaultdict(list)

    # subscribe (topic, callback): Register a listener for a named event
    def subscribe(self, topic: str, callback: Callable):
        self._subscribers[topic].append(callback)

    # unsubscribe (topic, callback): Remove a previously registered listener
    def unsubscribe(self, topic, callback: Callable):
        self._subscribers[topic] = [
            cb for cb in self._subscribers[topic] if cb is not callback
        ]

    # publish (topic, *payload): Fire all listeners registered under a topic
    def publish(self, topic: str, *args: Any, **kwargs: Any):
        for cb in self._subscribers.get(topic, []):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                log.error(f"EventBus error [{topic}]: {e}")


# Event topic constants — keeps magic strings in one place
class Events:
    SCREEN_CHANGE       = "screen.change"
    SIM_TICK            = "sim.tick"
    SIM_STARTED         = "sim.started"
    SIM_PAUSED          = "sim.paused"
    SIM_RESUMED         = "sim.resumed"
    SIM_COMPLETED       = "sim.completed"
    SIM_ABORTED         = "sim.aborted"
    SIM_SPEED_CHANGED   = "sim.speed_changed"
    BATCH_READY         = "batch.ready"
    MODIFIER_READY      = "modifier.ready"
    TRIAL_SAVED         = "trial.saved"
    GTFS_LOADED         = "gtfs.loaded"