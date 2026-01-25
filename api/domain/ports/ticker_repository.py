from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.security import Security
from domain.value_objects import ValidatedTicker, UserAddedTicker


class TickerRepository(ABC):
    """Port for ticker persistence operations."""

    @abstractmethod
    def ticker_exists(self, ticker: str) -> bool:
        """Check if ticker already exists in equity_details."""
        pass

    @abstractmethod
    def add_security(self, validated: ValidatedTicker) -> UUID:
        """
        Add a validated ticker to the security registry.

        Returns:
            security_id of the created security
        """
        pass

    @abstractmethod
    def get_user_added_tickers(self) -> list[UserAddedTicker]:
        """Get all tickers added by users (source='user')."""
        pass

    @abstractmethod
    def get_all_securities(self) -> list[Security]:
        """Get all securities from the registry with their details."""
        pass
