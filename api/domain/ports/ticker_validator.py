from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ValidatedTicker:
    """Represents a validated ticker with metadata from external source."""

    ticker: str
    display_name: str
    asset_type: str  # 'EQUITY', 'ETF'
    exchange: str | None
    sector: str | None
    industry: str | None
    currency: str


class TickerValidator(ABC):
    """Port for validating tickers against external data sources."""

    @abstractmethod
    def validate(self, ticker: str) -> ValidatedTicker | None:
        """
        Validate a ticker symbol and retrieve its metadata.

        Args:
            ticker: Stock/ETF ticker symbol

        Returns:
            ValidatedTicker if valid, None if invalid or not found
        """
        pass
