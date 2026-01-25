from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AddTickerRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)


class AddTickerResponse(BaseModel):
    ticker: str
    display_name: str
    asset_type: str
    exchange: str | None
    message: str


class UserAddedTickerResponse(BaseModel):
    ticker: str
    display_name: str
    asset_type: str
    added_at: datetime


class UserAddedTickersListResponse(BaseModel):
    tickers: list[UserAddedTickerResponse]
    count: int


class SecurityResponse(BaseModel):
    """Response schema for a security in the registry."""

    security_id: UUID
    ticker: str
    display_name: str
    asset_type: str
    currency: str
    sector: str | None = None
    industry: str | None = None
    exchange: str | None = None


class SecurityRegistryResponse(BaseModel):
    """Response schema for the security registry."""

    securities: list[SecurityResponse]
    count: int
