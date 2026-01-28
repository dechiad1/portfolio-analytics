from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.models.holding import Holding
from domain.services.holding_service import (
    HoldingNotFoundError,
    HoldingService,
    HoldingValidationError,
)


@pytest.fixture
def portfolio_id():
    return uuid4()


@pytest.fixture
def holding_id():
    return uuid4()


@pytest.fixture
def sample_holding(holding_id, portfolio_id):
    return Holding(
        id=holding_id,
        portfolio_id=portfolio_id,
        ticker="AAPL",
        name="Apple Inc.",
        asset_type="equity",
        asset_class="US Large Cap",
        sector="Technology",
        broker="Fidelity",
        quantity=Decimal("10"),
        purchase_price=Decimal("150.00"),
        current_price=Decimal("175.00"),
        purchase_date=date(2024, 1, 15),
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_repository(sample_holding):
    repo = MagicMock()
    repo.create.side_effect = lambda h: h
    repo.update.side_effect = lambda h: h
    repo.get_by_id.return_value = sample_holding
    repo.get_by_portfolio_id.return_value = [sample_holding]
    repo.get_all.return_value = [sample_holding]
    repo.bulk_create.side_effect = lambda h: h
    return repo


@pytest.fixture
def holding_service(mock_repository):
    return HoldingService(holding_repository=mock_repository)


class TestCreateHolding:
    def test_creates_valid_holding(self, holding_service, portfolio_id):
        result = holding_service.create_holding(
            portfolio_id=portfolio_id,
            ticker="msft",
            name="Microsoft",
            asset_type="equity",
            asset_class="US Large Cap",
            sector="Technology",
            broker="Fidelity",
            quantity=Decimal("5"),
            purchase_price=Decimal("300"),
            purchase_date=date(2024, 6, 1),
        )
        assert result.ticker == "MSFT"
        assert result.name == "Microsoft"

    def test_raises_on_empty_ticker(self, holding_service, portfolio_id):
        with pytest.raises(HoldingValidationError, match="ticker"):
            holding_service.create_holding(
                portfolio_id=portfolio_id,
                ticker="",
                name="Name",
                asset_type="equity",
                asset_class="Class",
                sector="Sector",
                broker="Broker",
                quantity=Decimal("1"),
                purchase_price=Decimal("10"),
                purchase_date=date(2024, 1, 1),
            )

    def test_raises_on_invalid_asset_type(self, holding_service, portfolio_id):
        with pytest.raises(HoldingValidationError, match="asset_type"):
            holding_service.create_holding(
                portfolio_id=portfolio_id,
                ticker="X",
                name="Name",
                asset_type="crypto",
                asset_class="Class",
                sector="Sector",
                broker="Broker",
                quantity=Decimal("1"),
                purchase_price=Decimal("10"),
                purchase_date=date(2024, 1, 1),
            )

    def test_raises_on_negative_quantity(self, holding_service, portfolio_id):
        with pytest.raises(HoldingValidationError, match="quantity"):
            holding_service.create_holding(
                portfolio_id=portfolio_id,
                ticker="X",
                name="Name",
                asset_type="equity",
                asset_class="Class",
                sector="Sector",
                broker="Broker",
                quantity=Decimal("-1"),
                purchase_price=Decimal("10"),
                purchase_date=date(2024, 1, 1),
            )

    def test_raises_on_negative_purchase_price(self, holding_service, portfolio_id):
        with pytest.raises(HoldingValidationError, match="purchase_price"):
            holding_service.create_holding(
                portfolio_id=portfolio_id,
                ticker="X",
                name="Name",
                asset_type="equity",
                asset_class="Class",
                sector="Sector",
                broker="Broker",
                quantity=Decimal("1"),
                purchase_price=Decimal("-5"),
                purchase_date=date(2024, 1, 1),
            )


class TestUpdateHolding:
    def test_updates_partial_fields(self, holding_service, holding_id):
        result = holding_service.update_holding(holding_id, name="Apple Computer")
        assert result.name == "Apple Computer"
        assert result.ticker == "AAPL"  # unchanged

    def test_raises_when_not_found(self, holding_service, mock_repository):
        mock_repository.get_by_id.return_value = None
        with pytest.raises(HoldingNotFoundError):
            holding_service.update_holding(uuid4(), name="X")


class TestDeleteHolding:
    def test_deletes_existing(self, holding_service, holding_id, mock_repository):
        holding_service.delete_holding(holding_id)
        mock_repository.delete.assert_called_once_with(holding_id)

    def test_raises_when_not_found(self, holding_service, mock_repository):
        mock_repository.get_by_id.return_value = None
        with pytest.raises(HoldingNotFoundError):
            holding_service.delete_holding(uuid4())


class TestGetHolding:
    def test_returns_holding(self, holding_service, sample_holding):
        result = holding_service.get_holding(sample_holding.id)
        assert result.ticker == "AAPL"

    def test_returns_none_when_not_found(self, holding_service, mock_repository):
        mock_repository.get_by_id.return_value = None
        assert holding_service.get_holding(uuid4()) is None


class TestParseCSV:
    def test_parses_valid_csv(self, holding_service, portfolio_id):
        csv = (
            "ticker,name,asset_type,asset_class,sector,broker,quantity,purchase_price,purchase_date\n"
            "AAPL,Apple Inc.,equity,US Large Cap,Technology,Fidelity,10,150.00,2024-01-15\n"
            "MSFT,Microsoft,equity,US Large Cap,Technology,Fidelity,5,300.00,2024-02-01\n"
        )
        result = holding_service.parse_and_create_holdings_from_csv(portfolio_id, csv)
        assert len(result) == 2
        assert result[0].ticker == "AAPL"
        assert result[1].ticker == "MSFT"

    def test_raises_on_missing_columns(self, holding_service, portfolio_id):
        csv = "ticker,name\nAAPL,Apple\n"
        with pytest.raises(HoldingValidationError, match="missing required columns"):
            holding_service.parse_and_create_holdings_from_csv(portfolio_id, csv)

    def test_raises_on_empty_csv(self, holding_service, portfolio_id):
        csv = "ticker,name,asset_type,asset_class,sector,broker,quantity,purchase_price,purchase_date\n"
        with pytest.raises(HoldingValidationError, match="no data rows"):
            holding_service.parse_and_create_holdings_from_csv(portfolio_id, csv)

    def test_raises_on_no_headers(self, holding_service, portfolio_id):
        with pytest.raises(HoldingValidationError, match="empty or has no headers"):
            holding_service.parse_and_create_holdings_from_csv(portfolio_id, "")

    def test_raises_on_invalid_date(self, holding_service, portfolio_id):
        csv = (
            "ticker,name,asset_type,asset_class,sector,broker,quantity,purchase_price,purchase_date\n"
            "AAPL,Apple,equity,Cap,Tech,Broker,10,150,not-a-date\n"
        )
        with pytest.raises(HoldingValidationError, match="Invalid date format"):
            holding_service.parse_and_create_holdings_from_csv(portfolio_id, csv)

    def test_parses_optional_current_price(self, holding_service, portfolio_id):
        csv = (
            "ticker,name,asset_type,asset_class,sector,broker,quantity,purchase_price,purchase_date,current_price\n"
            "AAPL,Apple,equity,Cap,Tech,Broker,10,150,2024-01-15,175.50\n"
        )
        result = holding_service.parse_and_create_holdings_from_csv(portfolio_id, csv)
        assert result[0].current_price == Decimal("175.50")


class TestParseDate:
    def test_valid_date(self, holding_service):
        assert holding_service._parse_date("2024-06-15") == date(2024, 6, 15)

    def test_invalid_date(self, holding_service):
        with pytest.raises(HoldingValidationError, match="Invalid date format"):
            holding_service._parse_date("15/06/2024")


class TestValidateHoldingData:
    def test_multiple_errors_combined(self, holding_service):
        with pytest.raises(HoldingValidationError) as exc_info:
            holding_service._validate_holding_data(
                ticker="",
                name="",
                asset_type="",
                asset_class="",
                sector="",
                broker="",
                quantity=Decimal("-1"),
                purchase_price=Decimal("-1"),
            )
        msg = str(exc_info.value)
        assert "ticker" in msg
        assert "name" in msg
        assert "quantity" in msg
