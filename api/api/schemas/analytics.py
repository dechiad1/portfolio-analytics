from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class HoldingAnalyticsResponse(BaseModel):
    """Response schema for individual holding analytics."""

    ticker: str
    name: str
    asset_class: str
    sector: str
    broker: str
    purchase_date: date
    latest_return: Decimal | None = None
    cumulative_return: Decimal | None = None
    volatility: Decimal | None = None
    expense_ratio: Decimal | None = None
    category: str | None = None


class AnalyticsResponse(BaseModel):
    """Response schema for portfolio analytics."""

    session_id: UUID
    total_holdings: int
    holdings: list[HoldingAnalyticsResponse]
    portfolio_avg_return: Decimal | None = None
    portfolio_avg_volatility: Decimal | None = None
    asset_class_breakdown: dict[str, int]
    sector_breakdown: dict[str, int]
    broker_breakdown: dict[str, int]
