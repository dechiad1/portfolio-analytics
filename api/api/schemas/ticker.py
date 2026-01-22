from datetime import datetime

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
