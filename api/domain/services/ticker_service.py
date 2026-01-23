from domain.exceptions import TickerAlreadyTrackedException, InvalidTickerException
from domain.ports.ticker_repository import TickerRepository
from domain.ports.ticker_validator import TickerValidator
from domain.value_objects import ValidatedTicker, UserAddedTicker


class TickerService:
    """Service for adding new tickers to tracking."""

    def __init__(
        self,
        validator: TickerValidator,
        repository: TickerRepository,
    ) -> None:
        self._validator = validator
        self._repository = repository

    def get_user_added_tickers(self) -> list[UserAddedTicker]:
        """Get all tickers that were manually added by users."""
        return self._repository.get_user_added_tickers()

    def add_ticker(self, ticker: str) -> ValidatedTicker:
        """
        Validate and add a ticker to the security registry.

        Args:
            ticker: The ticker symbol to add

        Returns:
            ValidatedTicker with the added ticker's metadata

        Raises:
            TickerAlreadyTrackedException: If ticker is already being tracked
            InvalidTickerException: If ticker cannot be validated
        """
        ticker_upper = ticker.upper().strip()

        # Check if already tracked
        if self._repository.ticker_exists(ticker_upper):
            raise TickerAlreadyTrackedException(ticker_upper)

        # Validate via external service
        validated = self._validator.validate(ticker_upper)
        if validated is None:
            raise InvalidTickerException(ticker_upper, "not found on Yahoo Finance")

        # Persist to database
        self._repository.add_security(validated)

        return validated
