from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.position import Position


class PositionRepository(ABC):
    """Port for position persistence operations."""

    @abstractmethod
    def get_by_portfolio_id(self, portfolio_id: UUID) -> list[Position]:
        """Retrieve all positions for a portfolio."""
        pass

    @abstractmethod
    def get_by_portfolio_and_security(
        self, portfolio_id: UUID, security_id: UUID
    ) -> Position | None:
        """Retrieve a specific position."""
        pass

    @abstractmethod
    def upsert(self, position: Position) -> Position:
        """Create or update a position."""
        pass

    @abstractmethod
    def delete(self, portfolio_id: UUID, security_id: UUID) -> None:
        """Delete a position."""
        pass

    @abstractmethod
    def bulk_upsert(self, positions: list[Position]) -> list[Position]:
        """Create or update multiple positions."""
        pass
