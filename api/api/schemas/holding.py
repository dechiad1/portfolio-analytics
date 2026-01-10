from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateHoldingRequest(BaseModel):
    """Request schema for creating a holding."""

    ticker: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    asset_class: str = Field(..., min_length=1, max_length=100)
    sector: str = Field(..., min_length=1, max_length=100)
    broker: str = Field(..., min_length=1, max_length=100)
    purchase_date: date


class UpdateHoldingRequest(BaseModel):
    """Request schema for updating a holding."""

    ticker: str | None = Field(None, min_length=1, max_length=20)
    name: str | None = Field(None, min_length=1, max_length=255)
    asset_class: str | None = Field(None, min_length=1, max_length=100)
    sector: str | None = Field(None, min_length=1, max_length=100)
    broker: str | None = Field(None, min_length=1, max_length=100)
    purchase_date: date | None = None


class HoldingResponse(BaseModel):
    """Response schema for a holding."""

    id: UUID
    session_id: UUID
    ticker: str
    name: str
    asset_class: str
    sector: str
    broker: str
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
