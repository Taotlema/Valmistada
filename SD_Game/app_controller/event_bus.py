# event_bus: Lightweight pub-sub bus keeping all cross-module communication in one place.

from collections import defaultdict
from typing import Callable, Any
import logging

log = logging.getLogger(__name__)


# Events: All topic-string constants used across the application.
class Events:
    SCREEN_CHANGE     = "screen.change"
    SIM_TICK          = "sim.tick"
    SIM_STARTED       = "sim.started"
    SIM_PAUSED        = "sim.paused"
    SIM_RESUMED       = "sim.resumed"
    SIM_COMPLETED     = "sim.completed"
    SIM_ABORTED       = "sim.aborted"
    SIM_SPEED_CHANGED = "sim.speed_changed"
    BATCH_READY       = "batch.ready"
    MODIFIER_READY    = "modifier.ready"
    TRIAL_SAVED       = "trial.saved"
    GTFS_LOADED       = "gtfs.loaded"


# EventBus: Delivers published events to all registered subscriber callbacks.
class EventBus:

    def __init__(self):
        # Maps topic string to list of registered callbacks
        self._subscribers: dict = defaultdict(list)

    # subscribe: Register a callback for a named topic.
    def subscribe(self, topic: str, callback: Callable):
        self._subscribers[topic].append(callback)

    # unsubscribe: Remove a previously registered callback.
    def unsubscribe(self, topic: str, callback: Callable):
        self._subscribers[topic] = [
            cb for cb in self._subscribers[topic] if cb is not callback
        ]

    # publish: Call every subscriber registered under topic with the given args.
    def publish(self, topic: str, *args: Any, **kwargs: Any):
        for cb in list(self._subscribers.get(topic, [])):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                log.error(f"EventBus [{topic}]: {e}")
