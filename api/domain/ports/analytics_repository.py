from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TickerPerformance(BaseModel):
    """Performance data for a single ticker."""

    ticker: str
    date: date
    daily_return: Decimal
    cumulative_return: Decimal
    volatility: Decimal | None = None

    model_config = {"frozen": True}


class FundMetadata(BaseModel):
    """Metadata for a fund/ticker."""

    ticker: str
    name: str
    asset_class: str
    category: str | None = None
    expense_ratio: Decimal | None = None
    inception_date: date | None = None

    model_config = {"frozen": True}


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
