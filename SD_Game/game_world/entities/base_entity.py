"""
Filename: base_entity.py
Author: Ayemhenre Isikhuemhen
Description: Abstract base class all game-world entities inherit from.
Last Updated: March, 2026
"""

# Libraries
from abc import ABC, abstractmethod


# BaseEntity: Provides a unique ID and tick update contract for all sim objects
class BaseEntity(ABC):

    _id_counter: int = 0

    # __init__ (entity_id: optional custom id)
    def __init__(self, entity_id: str = None):
        BaseEntity._id_counter += 1
        self.entity_id: str = entity_id or f"entity_{BaseEntity._id_counter}"
        self.active: bool   = True

    # update (tick, dt): Called once per simulation tick — must be overridden
    @abstractmethod
    def update(self, tick: int, dt: float):
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.entity_id} active={self.active}>"