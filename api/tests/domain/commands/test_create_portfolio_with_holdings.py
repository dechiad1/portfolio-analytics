from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.commands.create_portfolio_with_holdings import (
    CreatePortfolioWithHoldingsCommand,
)
from domain.services.portfolio_builder_service import AllocationItem, PortfolioAllocation
from domain.value_objects import TickerDetails


@pytest.fixture
def mock_unit_of_work():
    uow = MagicMock()
    ctx = MagicMock()
    uow.transaction.return_value.__enter__ = MagicMock(return_value=ctx)
    uow.transaction.return_value.__exit__ = MagicMock(return_value=False)
    return uow


@pytest.fixture
def mock_portfolio_builder_repository():
    repo = MagicMock()
    now = datetime.now(timezone.utc)
    pid = uuid4()
    uid = uuid4()
    repo.create_portfolio_in_transaction.return_value = (
        pid, uid, "Test Portfolio", "USD", now, now
    )
    repo.find_security_by_ticker.return_value = uuid4()
    return repo


@pytest.fixture
def mock_analytics_repository():
    repo = MagicMock()
    repo.get_ticker_details.return_value = TickerDetails(
        ticker="AAPL",
        name="Apple Inc.",
        asset_class="U.S. Stocks",
        sector="Technology",
        latest_price=Decimal("175.00"),
    )
    return repo


@pytest.fixture
def command(mock_unit_of_work, mock_portfolio_builder_repository, mock_analytics_repository):
    return CreatePortfolioWithHoldingsCommand(
        unit_of_work=mock_unit_of_work,
        portfolio_builder_repository=mock_portfolio_builder_repository,
        analytics_repository=mock_analytics_repository,
    )


@pytest.fixture
def sample_allocation():
    return PortfolioAllocation(
        allocations=[
            AllocationItem(
                ticker="AAPL",
                display_name="Apple Inc.",
                asset_type="EQUITY",
                sector="Technology",
                weight=Decimal("60"),
                value=Decimal("6000"),
            ),
            AllocationItem(
                ticker="BND",
                display_name="Vanguard Bond",
                asset_type="ETF",
                sector="Bonds",
                weight=Decimal("40"),
                value=Decimal("4000"),
            ),
        ],
        total_value=Decimal("10000"),
        unmatched_descriptions=["some unknown thing"],
    )


class TestExecute:
    def test_creates_portfolio_without_allocation(self, command):
        result = command.execute(
            user_id=uuid4(),
            name="Empty Portfolio",
            base_currency="USD",
        )
        assert result.portfolio is not None
        assert result.holdings_created == 0
        assert result.unmatched_descriptions == []

    def test_creates_portfolio_with_allocation(self, command, sample_allocation):
        result = command.execute(
            user_id=uuid4(),
            name="Full Portfolio",
            base_currency="USD",
            allocation=sample_allocation,
        )
        assert result.holdings_created == 2
        assert "some unknown thing" in result.unmatched_descriptions

    def test_uses_default_price_when_not_available(
        self, command, sample_allocation, mock_analytics_repository
    ):
        mock_analytics_repository.get_ticker_details.return_value = None
        result = command.execute(
            user_id=uuid4(),
            name="Portfolio",
            base_currency="USD",
            allocation=sample_allocation,
        )
        assert result.holdings_created == 2
        assert any("Price not available" in d for d in result.unmatched_descriptions)

    def test_handles_holding_creation_failure(
        self, command, sample_allocation, mock_portfolio_builder_repository
    ):
        mock_portfolio_builder_repository.create_position_in_transaction.side_effect = [
            None,
            Exception("DB error"),
        ]
        result = command.execute(
            user_id=uuid4(),
            name="Portfolio",
            base_currency="USD",
            allocation=sample_allocation,
        )
        # First succeeds, second fails
        assert result.holdings_created == 1
        assert any("Failed to add BND" in d for d in result.unmatched_descriptions)

    def test_creates_new_security_when_not_found(
        self, command, sample_allocation, mock_portfolio_builder_repository
    ):
        mock_portfolio_builder_repository.find_security_by_ticker.return_value = None
        command.execute(
            user_id=uuid4(),
            name="Portfolio",
            base_currency="USD",
            allocation=sample_allocation,
        )
        assert mock_portfolio_builder_repository.create_security_in_transaction.call_count == 2
