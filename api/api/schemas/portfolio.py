from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreatePortfolioRequest(BaseModel):
    """Request schema for creating a portfolio."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class UpdatePortfolioRequest(BaseModel):
    """Request schema for updating a portfolio."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class PortfolioResponse(BaseModel):
    """Response schema for a portfolio."""

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class PortfolioListResponse(BaseModel):
    """Response schema for a list of portfolios."""

    portfolios: list[PortfolioResponse]
    count: int


class AssetBreakdown(BaseModel):
    """Breakdown of assets by category."""

    name: str
    value: float
    percentage: float


class PortfolioSummaryResponse(BaseModel):
    """Response schema for portfolio summary with breakdowns."""

    portfolio_id: str
    portfolio_name: str
    total_value: float
    total_cost: float
    total_gain_loss: float
    total_gain_loss_percent: float
    holdings_count: int
    by_asset_type: list[AssetBreakdown]
    by_asset_class: list[AssetBreakdown]
    by_sector: list[AssetBreakdown]
