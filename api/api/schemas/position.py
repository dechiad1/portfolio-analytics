from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AddPositionRequest(BaseModel):
    """Request schema for adding a position."""

    ticker: str = Field(..., min_length=1, max_length=20)
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)
    event_date: date


class PositionResponse(BaseModel):
    """Response schema for a position."""

    portfolio_id: str
    security_id: str
    ticker: str
    name: str
    asset_type: str
    sector: str | None
    quantity: float
    avg_cost: float
    current_price: float | None
    market_value: float | None
    cost_basis: float
    gain_loss: float | None
    gain_loss_pct: float | None


class PositionListResponse(BaseModel):
    """Response schema for a list of positions."""

    positions: list[PositionResponse]
    count: int


class TransactionResponse(BaseModel):
    """Response schema for a transaction."""

    txn_id: str
    portfolio_id: str
    security_id: str | None
    txn_type: str
    quantity: float
    price: float | None
    fees: float
    event_ts: datetime
    notes: str | None


class TransactionListResponse(BaseModel):
    """Response schema for a list of transactions."""

    transactions: list[TransactionResponse]
    count: int
