from typing import Annotated

from fastapi import APIRouter, Depends

from api.schemas.ticker import (
    AddTickerRequest,
    AddTickerResponse,
    UserAddedTickersListResponse,
)
from dependencies import get_ticker_service
from domain.services.ticker_service import TickerService

router = APIRouter(prefix="/tickers", tags=["tickers"])


@router.get("/user-added", response_model=UserAddedTickersListResponse)
def get_user_added_tickers(
    ticker_service: Annotated[TickerService, Depends(get_ticker_service)],
) -> UserAddedTickersListResponse:
    """
    Get all tickers that were manually added by users.

    These tickers may not yet have data if a refresh hasn't been run.
    """
    return ticker_service.get_user_added_tickers()


@router.post("/track", response_model=AddTickerResponse)
def add_ticker(
    request: AddTickerRequest,
    ticker_service: Annotated[TickerService, Depends(get_ticker_service)],
) -> AddTickerResponse:
    """
    Add a ticker to be tracked. Validates via Yahoo Finance before adding.

    Returns ticker details on success.
    Raises 400 if ticker is invalid or already tracked.
    """
    return ticker_service.add_ticker(request.ticker)
