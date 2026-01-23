"""Domain-specific exceptions.

These exceptions represent business rule violations and domain errors.
API layer should catch these and translate to appropriate HTTP responses.
"""


class DomainException(Exception):
    """Base exception for domain errors."""

    pass


class TickerAlreadyTrackedException(DomainException):
    """Raised when attempting to add a ticker that is already being tracked."""

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        super().__init__(f"Ticker {ticker} is already being tracked")


class InvalidTickerException(DomainException):
    """Raised when a ticker cannot be validated against external sources."""

    def __init__(self, ticker: str, reason: str = "not found") -> None:
        self.ticker = ticker
        self.reason = reason
        super().__init__(f"Invalid ticker: {ticker} ({reason})")
