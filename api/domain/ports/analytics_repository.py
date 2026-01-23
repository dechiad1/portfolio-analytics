from abc import ABC, abstractmethod
from datetime import date

from domain.value_objects import (
    TickerPerformance,
    FundMetadata,
    TickerDetails,
    TickerPriceAtDate,
)


class AnalyticsRepository(ABC):
    """Port for analytics data retrieval from the data warehouse."""

    @abstractmethod
    def get_performance_for_tickers(
        self, tickers: list[str]
    ) -> list[TickerPerformance]:
        """Retrieve performance data for the given tickers."""
        pass

    @abstractmethod
    def get_fund_metadata_for_tickers(self, tickers: list[str]) -> list[FundMetadata]:
        """Retrieve fund metadata for the given tickers."""
        pass

    @abstractmethod
    def search_tickers(self, query: str, limit: int = 20) -> list[FundMetadata]:
        """Search for tickers by name or ticker symbol. Returns up to limit results."""
        pass

    @abstractmethod
    def get_all_securities(self) -> list[tuple[FundMetadata, TickerPerformance | None]]:
        """Retrieve all securities with their performance data."""
        pass

    @abstractmethod
    def get_ticker_details(self, ticker: str) -> TickerDetails | None:
        """Get detailed ticker info including latest price for holding creation."""
        pass

    @abstractmethod
    def get_price_for_date(self, ticker: str, price_date: date) -> TickerPriceAtDate | None:
        """Get the price for a ticker at or before a specific date."""
        pass
