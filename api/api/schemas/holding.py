from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateHoldingRequest(BaseModel):
    """Request schema for creating a holding."""

    ticker: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    asset_type: str = Field(..., min_length=1, max_length=50)
    asset_class: str = Field(..., min_length=1, max_length=100)
    sector: str = Field(..., min_length=1, max_length=100)
    broker: str = Field(..., min_length=1, max_length=100)
    quantity: Decimal = Field(..., ge=0)
    purchase_price: Decimal = Field(..., ge=0)
    current_price: Decimal | None = Field(None, ge=0)
    purchase_date: date


class UpdateHoldingRequest(BaseModel):
    """Request schema for updating a holding."""

    ticker: str | None = Field(None, min_length=1, max_length=20)
    name: str | None = Field(None, min_length=1, max_length=255)
    asset_type: str | None = Field(None, min_length=1, max_length=50)
    asset_class: str | None = Field(None, min_length=1, max_length=100)
    sector: str | None = Field(None, min_length=1, max_length=100)
    broker: str | None = Field(None, min_length=1, max_length=100)
    quantity: Decimal | None = Field(None, ge=0)
    purchase_price: Decimal | None = Field(None, ge=0)
    current_price: Decimal | None = Field(None, ge=0)
    purchase_date: date | None = None


class HoldingResponse(BaseModel):
    """Response schema for a holding."""

    id: UUID
    portfolio_id: UUID | None
    ticker: str
    name: str
    asset_type: str
    asset_class: str
    sector: str
    broker: str
    quantity: float
    purchase_price: float
    current_price: float | None
    market_value: float
    cost_basis: float
    gain_loss: float
    purchase_date: date
    created_at: datetime


class HoldingListResponse(BaseModel):
    """Response schema for a list of holdings."""

    holdings: list[HoldingResponse]
    count: int


class BulkCreateHoldingsResponse(BaseModel):
    """Response schema for bulk holding creation."""

    created_count: int
    holdings: list[HoldingResponse]
