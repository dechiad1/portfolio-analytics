from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TickerPerformance(BaseModel):
    """Aggregated performance data for a single ticker."""

    ticker: str
    # Legacy fields (for backwards compatibility)
    total_return_pct: Decimal
    annualized_return_pct: Decimal
    volatility_pct: Decimal | None = None
    sharpe_ratio: Decimal | None = None
    vs_benchmark_pct: Decimal | None = None
    # 1-Year metrics
    total_return_1y_pct: Decimal | None = None
    return_vs_risk_free_1y_pct: Decimal | None = None
    return_vs_sp500_1y_pct: Decimal | None = None
    volatility_1y_pct: Decimal | None = None
    sharpe_ratio_1y: Decimal | None = None
    # 5-Year metrics
    total_return_5y_pct: Decimal | None = None
    return_vs_risk_free_5y_pct: Decimal | None = None
    return_vs_sp500_5y_pct: Decimal | None = None
    volatility_5y_pct: Decimal | None = None
    sharpe_ratio_5y: Decimal | None = None

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


class TickerDetails(BaseModel):
    """Detailed ticker information with pricing data for holding creation."""

    ticker: str
    name: str
    asset_class: str
    sector: str | None = None
    category: str | None = None
    latest_price: Decimal | None = None
    latest_price_date: date | None = None

    model_config = {"frozen": True}


class TickerPriceAtDate(BaseModel):
    """Price information for a ticker at a specific date."""

    ticker: str
    price_date: date
    price: Decimal

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
