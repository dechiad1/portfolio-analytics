from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class TickerSearchResult(BaseModel):
    """Response schema for ticker search result."""

    ticker: str
    name: str
    asset_class: str
    category: str | None = None


class TickerSearchResponse(BaseModel):
    """Response schema for ticker search."""

    results: list[TickerSearchResult]
    count: int


class TickerAnalyticsResponse(BaseModel):
    """Response schema for individual ticker analytics."""

    ticker: str
    name: str
    asset_class: str
    sector: str
    total_return_pct: float
    annualized_return_pct: float
    volatility_pct: float
    sharpe_ratio: float
    vs_benchmark_pct: float
    expense_ratio: float | None = None


class AssetClassBreakdownResponse(BaseModel):
    """Response schema for asset class breakdown."""

    asset_class: str
    count: int
    avg_return: float


class SectorBreakdownResponse(BaseModel):
    """Response schema for sector breakdown."""

    sector: str
    count: int
    avg_return: float


class AnalyticsResponse(BaseModel):
    """Response schema for portfolio analytics."""

    holdings_count: int
    avg_total_return_pct: float
    avg_annualized_return_pct: float
    avg_sharpe_ratio: float
    beat_benchmark_count: int
    holdings: list[TickerAnalyticsResponse]
    asset_class_breakdown: list[AssetClassBreakdownResponse]
    sector_breakdown: list[SectorBreakdownResponse]
