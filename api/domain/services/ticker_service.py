from fastapi import HTTPException

from api.schemas.ticker import (
    AddTickerResponse,
    UserAddedTickerResponse,
    UserAddedTickersListResponse,
)
from domain.ports.ticker_repository import TickerRepository
from domain.ports.ticker_validator import TickerValidator


class TickerService:
    """Service for adding new tickers to tracking."""

    def __init__(
        self,
        validator: TickerValidator,
        repository: TickerRepository,
    ) -> None:
        self._validator = validator
        self._repository = repository

    def get_user_added_tickers(self) -> UserAddedTickersListResponse:
        """Get all tickers that were manually added by users."""
        tickers = self._repository.get_user_added_tickers()
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

    def add_ticker(self, ticker: str) -> AddTickerResponse:
        """
        Validate and add a ticker to the security registry.

        Raises:
            HTTPException(400): Ticker already tracked
            HTTPException(400): Invalid ticker
        """
        ticker_upper = ticker.upper().strip()

        # Check if already tracked
        if self._repository.ticker_exists(ticker_upper):
            raise HTTPException(
                status_code=400,
                detail=f"Ticker {ticker_upper} is already being tracked",
            )

        # Validate via external service
        validated = self._validator.validate(ticker_upper)
        if validated is None:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ticker: {ticker_upper} not found on Yahoo Finance",
            )

        # Persist to database
        self._repository.add_security(validated)

        return AddTickerResponse(
            ticker=validated.ticker,
            display_name=validated.display_name,
            asset_type=validated.asset_type,
            exchange=validated.exchange,
            message=f"Successfully added {validated.ticker}. Run 'task refresh' to fetch historical data.",
        )
