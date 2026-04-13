# base_entity: Abstract base class all simulation entities inherit from.

from abc import ABC, abstractmethod


# BaseEntity: Provides a unique ID and an active flag for every entity.
class BaseEntity(ABC):

    _id_counter: int = 0

    def __init__(self, entity_id: str = None):
        BaseEntity._id_counter += 1
        self.entity_id: str = entity_id or f"entity_{BaseEntity._id_counter}"
        self.active:    bool = True

    # update: Called once per simulation tick; must be implemented by every subclass.
    @abstractmethod
    def update(self, tick: int, dt: float):
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.entity_id} active={self.active}>"
