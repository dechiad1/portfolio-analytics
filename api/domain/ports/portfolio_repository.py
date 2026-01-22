from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.portfolio import Portfolio


class PortfolioRepository(ABC):
    """Port for portfolio persistence operations."""

    @abstractmethod
    def create(self, portfolio: Portfolio) -> Portfolio:
        """Persist a new portfolio."""
        pass

    @abstractmethod
    def get_by_id(self, id: UUID) -> Portfolio | None:
        """Retrieve a portfolio by ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> list[Portfolio]:
        """Retrieve all portfolios for a user."""
        pass

    @abstractmethod
    def update(self, portfolio: Portfolio) -> Portfolio:
        """Update an existing portfolio."""
        pass

    @abstractmethod
    def delete(self, id: UUID) -> None:
        """Delete a portfolio by ID."""
        pass

    @abstractmethod
    def get_all_with_users(self) -> list[tuple["Portfolio", str]]:
        """Retrieve all portfolios with owner email."""
        pass
