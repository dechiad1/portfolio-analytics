"""Domain value objects - immutable data structures representing domain concepts."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


# Analytics value objects
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


# Ticker value objects
@dataclass(frozen=True)
class ValidatedTicker:
    """Represents a validated ticker with metadata from external source."""

    ticker: str
    display_name: str
    asset_type: str  # 'EQUITY', 'ETF'
    exchange: str | None
    sector: str | None
    industry: str | None
    currency: str


@dataclass(frozen=True)
class UserAddedTicker:
    """Represents a ticker added by a user."""

    ticker: str
    display_name: str
    asset_type: str
    added_at: datetime


# OAuth value objects
@dataclass(frozen=True)
class OAuthTokens:
    """OAuth tokens returned from provider."""

    access_token: str
    id_token: str
    refresh_token: str | None = None
    expires_in: int = 3600


@dataclass(frozen=True)
class OAuthUserInfo:
    """User information extracted from OAuth tokens."""

    subject: str
    email: str
    email_verified: bool = False
    name: str | None = None


@dataclass(frozen=True)
class EnrichedSecurity:
    """Enriched security data from analytics warehouse for scenario-based selection."""

    # Core identity
    ticker: str
    display_name: str
    asset_type: str
    sector: str | None
    industry: str | None
    country: str | None
    exchange: str | None
    # Market dynamics
    market_cap: float | None
    market_cap_category: str | None  # mega, large, mid, small, micro
    beta: float | None
    annualized_volatility: float | None
    # Valuation
    trailing_pe: float | None
    forward_pe: float | None
    price_to_book: float | None
    # Income
    dividend_yield: float | None
    # Profitability
    profit_margin: float | None
    return_on_equity: float | None
    # Growth
    revenue_growth: float | None
    # Financial health
    debt_to_equity: float | None
    # Scenario-relevant flags
    is_dividend_payer: bool
    is_high_growth: bool
    is_value: bool
    is_defensive: bool
    is_cyclical: bool
    is_rate_sensitive: bool
    is_inflation_hedge: bool
    # Historical performance
    historical_annual_return: float | None
    # Analyst sentiment
    analyst_implied_return: float | None
    analyst_count: int | None


__all__ = [
    "TickerPerformance",
    "FundMetadata",
    "TickerDetails",
    "TickerPriceAtDate",
    "ValidatedTicker",
    "UserAddedTicker",
    "OAuthTokens",
    "OAuthUserInfo",
    "EnrichedSecurity",
]
