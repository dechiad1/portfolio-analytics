from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.ports.ticker_validator import ValidatedTicker


@dataclass
class UserAddedTicker:
    """Represents a ticker added by a user."""

    ticker: str
    display_name: str
    asset_type: str
    added_at: datetime


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
