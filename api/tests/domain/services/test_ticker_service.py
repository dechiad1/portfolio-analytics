from unittest.mock import MagicMock
from datetime import datetime, timezone

import pytest

from domain.exceptions import InvalidTickerException, TickerAlreadyTrackedException
from domain.services.ticker_service import TickerService
from domain.value_objects import ValidatedTicker, UserAddedTicker


@pytest.fixture
def mock_validator():
    validator = MagicMock()
    validator.validate.return_value = ValidatedTicker(
        ticker="AAPL",
        display_name="Apple Inc.",
        asset_type="EQUITY",
        exchange="NASDAQ",
        sector="Technology",
        industry="Consumer Electronics",
        currency="USD",
    )
    return validator


@pytest.fixture
def mock_repository():
    repo = MagicMock()
    repo.ticker_exists.return_value = False
    repo.get_user_added_tickers.return_value = [
        UserAddedTicker(
            ticker="TSLA",
            display_name="Tesla Inc.",
            asset_type="EQUITY",
            added_at=datetime.now(timezone.utc),
        ),
    ]
    return repo


@pytest.fixture
def ticker_service(mock_validator, mock_repository):
    return TickerService(validator=mock_validator, repository=mock_repository)


class TestAddTicker:
    def test_validates_and_persists(self, ticker_service, mock_validator, mock_repository):
        result = ticker_service.add_ticker("aapl")
        assert result.ticker == "AAPL"
        mock_validator.validate.assert_called_once_with("AAPL")
        mock_repository.add_security.assert_called_once_with(result)

    def test_raises_when_already_tracked(self, ticker_service, mock_repository):
        mock_repository.ticker_exists.return_value = True
        with pytest.raises(TickerAlreadyTrackedException):
            ticker_service.add_ticker("AAPL")

    def test_raises_when_validation_fails(self, ticker_service, mock_validator):
        mock_validator.validate.return_value = None
        with pytest.raises(InvalidTickerException):
            ticker_service.add_ticker("FAKE")

    def test_uppercases_and_strips_ticker(self, ticker_service, mock_repository):
        ticker_service.add_ticker("  msft  ")
        mock_repository.ticker_exists.assert_called_once_with("MSFT")


class TestGetUserAddedTickers:
    def test_returns_tickers(self, ticker_service):
        result = ticker_service.get_user_added_tickers()
        assert len(result) == 1
        assert result[0].ticker == "TSLA"
