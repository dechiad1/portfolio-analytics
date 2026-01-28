from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.models.holding import Holding
from domain.models.portfolio import Portfolio
from domain.services.portfolio_service import (
    PortfolioAccessDeniedError,
    PortfolioNotFoundError,
    PortfolioService,
)


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def other_user_id():
    return uuid4()


@pytest.fixture
def portfolio_id():
    return uuid4()


@pytest.fixture
def mock_portfolio(portfolio_id, user_id):
    return Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
        base_currency="USD",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_holdings(portfolio_id):
    return [
        Holding(
            id=uuid4(),
            portfolio_id=portfolio_id,
            ticker="AAPL",
            name="Apple Inc.",
            asset_type="equity",
            asset_class="US Large Cap",
            sector="Technology",
            broker="Fidelity",
            quantity=Decimal("10"),
            purchase_price=Decimal("100"),
            current_price=Decimal("150"),
            purchase_date=date(2024, 1, 1),
            created_at=datetime.now(timezone.utc),
        ),
        Holding(
            id=uuid4(),
            portfolio_id=portfolio_id,
            ticker="BND",
            name="Vanguard Bond",
            asset_type="etf",
            asset_class="Bonds",
            sector="Bonds",
            broker="Fidelity",
            quantity=Decimal("20"),
            purchase_price=Decimal("50"),
            current_price=Decimal("50"),
            purchase_date=date(2024, 1, 1),
            created_at=datetime.now(timezone.utc),
        ),
    ]


@pytest.fixture
def mock_portfolio_repository(mock_portfolio):
    repo = MagicMock()
    repo.create.side_effect = lambda p: p
    repo.update.side_effect = lambda p: p
    repo.get_by_id.return_value = mock_portfolio
    repo.get_by_user_id.return_value = [mock_portfolio]
    repo.get_all_with_users.return_value = [(mock_portfolio, "test@example.com")]
    return repo


@pytest.fixture
def mock_holding_repository(mock_holdings):
    repo = MagicMock()
    repo.get_by_portfolio_id.return_value = mock_holdings
    return repo


@pytest.fixture
def portfolio_service(mock_portfolio_repository, mock_holding_repository):
    return PortfolioService(
        portfolio_repository=mock_portfolio_repository,
        holding_repository=mock_holding_repository,
    )


class TestCreatePortfolio:
    def test_creates_portfolio(self, portfolio_service, user_id):
        result = portfolio_service.create_portfolio(user_id, "My Portfolio")
        assert result.name == "My Portfolio"
        assert result.user_id == user_id
        assert result.base_currency == "USD"

    def test_uppercases_currency(self, portfolio_service, user_id):
        result = portfolio_service.create_portfolio(user_id, "P", base_currency="eur")
        assert result.base_currency == "EUR"

    def test_strips_name(self, portfolio_service, user_id):
        result = portfolio_service.create_portfolio(user_id, "  My Portfolio  ")
        assert result.name == "My Portfolio"


class TestGetPortfolio:
    def test_returns_portfolio_for_owner(self, portfolio_service, portfolio_id, user_id):
        result = portfolio_service.get_portfolio(portfolio_id, user_id)
        assert result.id == portfolio_id

    def test_raises_when_not_found(self, portfolio_service, mock_portfolio_repository, user_id):
        mock_portfolio_repository.get_by_id.return_value = None
        with pytest.raises(PortfolioNotFoundError):
            portfolio_service.get_portfolio(uuid4(), user_id)

    def test_raises_when_not_owner(self, portfolio_service, portfolio_id, other_user_id):
        with pytest.raises(PortfolioAccessDeniedError):
            portfolio_service.get_portfolio(portfolio_id, other_user_id)

    def test_admin_can_access_any(self, portfolio_service, portfolio_id, other_user_id):
        result = portfolio_service.get_portfolio(portfolio_id, other_user_id, is_admin=True)
        assert result.id == portfolio_id


class TestGetUserPortfolios:
    def test_returns_user_portfolios(self, portfolio_service, user_id):
        result = portfolio_service.get_user_portfolios(user_id)
        assert len(result) == 1


class TestGetAllPortfoliosWithUsers:
    def test_admin_gets_all(self, portfolio_service, other_user_id):
        result = portfolio_service.get_all_portfolios_with_users(
            user_id=other_user_id, is_admin=True
        )
        assert len(result) == 1

    def test_non_admin_filtered(self, portfolio_service, other_user_id):
        result = portfolio_service.get_all_portfolios_with_users(
            user_id=other_user_id, is_admin=False
        )
        assert len(result) == 0

    def test_owner_sees_own(self, portfolio_service, user_id):
        result = portfolio_service.get_all_portfolios_with_users(
            user_id=user_id, is_admin=False
        )
        assert len(result) == 1


class TestUpdatePortfolio:
    def test_updates_name(self, portfolio_service, portfolio_id, user_id):
        result = portfolio_service.update_portfolio(portfolio_id, user_id, name="New Name")
        assert result.name == "New Name"

    def test_updates_currency(self, portfolio_service, portfolio_id, user_id):
        result = portfolio_service.update_portfolio(
            portfolio_id, user_id, base_currency="eur"
        )
        assert result.base_currency == "EUR"

    def test_raises_for_non_owner(self, portfolio_service, portfolio_id, other_user_id):
        with pytest.raises(PortfolioAccessDeniedError):
            portfolio_service.update_portfolio(portfolio_id, other_user_id, name="X")


class TestDeletePortfolio:
    def test_deletes_with_access(self, portfolio_service, portfolio_id, user_id, mock_portfolio_repository):
        portfolio_service.delete_portfolio(portfolio_id, user_id)
        mock_portfolio_repository.delete.assert_called_once_with(portfolio_id)

    def test_raises_for_non_owner(self, portfolio_service, portfolio_id, other_user_id):
        with pytest.raises(PortfolioAccessDeniedError):
            portfolio_service.delete_portfolio(portfolio_id, other_user_id)


class TestGetPortfolioHoldings:
    def test_returns_holdings(self, portfolio_service, portfolio_id, user_id):
        result = portfolio_service.get_portfolio_holdings(portfolio_id, user_id)
        assert len(result) == 2

    def test_raises_for_non_owner(self, portfolio_service, portfolio_id, other_user_id):
        with pytest.raises(PortfolioAccessDeniedError):
            portfolio_service.get_portfolio_holdings(portfolio_id, other_user_id)


class TestGetPortfolioSummary:
    def test_computes_totals(self, portfolio_service, portfolio_id, user_id):
        result = portfolio_service.get_portfolio_summary(portfolio_id, user_id)
        # AAPL: 10 * 150 = 1500, BND: 20 * 50 = 1000, total = 2500
        assert result["total_value"] == 2500.0
        # AAPL cost: 10 * 100 = 1000, BND cost: 20 * 50 = 1000, total = 2000
        assert result["total_cost"] == 2000.0
        assert result["total_gain_loss"] == 500.0
        assert result["holdings_count"] == 2

    def test_breakdowns_present(self, portfolio_service, portfolio_id, user_id):
        result = portfolio_service.get_portfolio_summary(portfolio_id, user_id)
        assert len(result["by_asset_type"]) == 2  # equity, etf
        assert len(result["by_sector"]) == 2  # Technology, Bonds

    def test_empty_portfolio(self, portfolio_service, portfolio_id, user_id, mock_holding_repository):
        mock_holding_repository.get_by_portfolio_id.return_value = []
        result = portfolio_service.get_portfolio_summary(portfolio_id, user_id)
        assert result["total_value"] == 0.0
        assert result["holdings_count"] == 0
        assert result["by_asset_type"] == []

    def test_gain_loss_percent(self, portfolio_service, portfolio_id, user_id):
        result = portfolio_service.get_portfolio_summary(portfolio_id, user_id)
        # (2500 - 2000) / 2000 * 100 = 25%
        assert result["total_gain_loss_percent"] == 25.0
