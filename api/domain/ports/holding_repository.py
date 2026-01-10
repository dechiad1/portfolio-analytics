from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.holding import Holding


class HoldingRepository(ABC):
    """Port for holding persistence operations."""

    @abstractmethod
    def create(self, holding: Holding) -> Holding:
        """Persist a new holding."""
        pass

    @abstractmethod
    def get_by_id(self, id: UUID) -> Holding | None:
        """Retrieve a holding by its ID."""
        pass

    @abstractmethod
    def get_by_session_id(self, session_id: UUID) -> list[Holding]:
        """Retrieve all holdings for a session."""
        pass

    @abstractmethod
    def update(self, holding: Holding) -> Holding:
        """Update an existing holding."""
        pass

    @abstractmethod
    def delete(self, id: UUID) -> None:
        """Delete a holding by its ID."""
        pass

    @abstractmethod
    def bulk_create(self, holdings: list[Holding]) -> list[Holding]:
        """Persist multiple holdings in a single operation."""
        pass
