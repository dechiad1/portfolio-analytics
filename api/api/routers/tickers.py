from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.ticker import (
    AddTickerRequest,
    AddTickerResponse,
    UserAddedTickerResponse,
    UserAddedTickersListResponse,
)
from dependencies import get_ticker_service
from domain.exceptions import TickerAlreadyTrackedException, InvalidTickerException
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
    tickers = ticker_service.get_user_added_tickers()
    return UserAddedTickersListResponse(
        tickers=[
            UserAddedTickerResponse(
                ticker=t.ticker,
                display_name=t.display_name,
                asset_type=t.asset_type,
                added_at=t.added_at,
            )
            for t in tickers
        ],
        count=len(tickers),
    )


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
    try:
        validated = ticker_service.add_ticker(request.ticker)
    except TickerAlreadyTrackedException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except InvalidTickerException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return AddTickerResponse(
        ticker=validated.ticker,
        display_name=validated.display_name,
        asset_type=validated.asset_type,
        exchange=validated.exchange,
        message=f"Successfully added {validated.ticker}. Run 'task refresh' to fetch historical data.",
    )
