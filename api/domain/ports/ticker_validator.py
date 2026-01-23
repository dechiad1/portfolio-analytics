from abc import ABC, abstractmethod

from domain.value_objects import ValidatedTicker


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
