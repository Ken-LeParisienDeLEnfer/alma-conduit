from abc import ABC, abstractmethod


class IModelMapper[M_, D_](ABC):
    """Interface for model mapping."""

    @staticmethod
    @abstractmethod
    def to_dto(model: M_) -> D_: ...

    @staticmethod
    @abstractmethod
    def from_dto(dto: D_) -> M_: ...
