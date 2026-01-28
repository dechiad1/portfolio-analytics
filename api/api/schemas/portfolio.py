from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


CreationMode = Literal["empty", "random", "dictation"]


class CreatePortfolioRequest(BaseModel):
    """Request schema for creating a portfolio."""

    name: str = Field(..., min_length=1, max_length=255)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    creation_mode: CreationMode = Field(default="empty")
    total_value: Decimal | None = Field(
        default=None,
        ge=Decimal("1000"),
        description="Total portfolio value for random/dictation mode (minimum 1000, default 100000)",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Portfolio description for dictation mode",
    )


class UpdatePortfolioRequest(BaseModel):
    """Request schema for updating a portfolio."""

    name: str | None = Field(None, min_length=1, max_length=255)
    base_currency: str | None = Field(None, min_length=3, max_length=3)


class PortfolioResponse(BaseModel):
    """Response schema for a portfolio."""

    id: UUID
    user_id: UUID
    name: str
    base_currency: str
    created_at: datetime
    updated_at: datetime


class CreatePortfolioResponse(BaseModel):
    """Response schema for portfolio creation with builder modes."""

    id: UUID
    user_id: UUID
    name: str
    base_currency: str
    created_at: datetime
    updated_at: datetime
    holdings_created: int = 0
    unmatched_descriptions: list[str] = []


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


class PortfolioWithUserResponse(BaseModel):
    """Response schema for a portfolio with user email."""

    id: UUID
    user_id: UUID
    user_email: str
    name: str
    base_currency: str
    created_at: datetime
    updated_at: datetime


class AllPortfoliosListResponse(BaseModel):
    """Response schema for a list of all portfolios with user info."""

    portfolios: list[PortfolioWithUserResponse]
    count: int
